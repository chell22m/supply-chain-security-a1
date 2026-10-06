import os
import argparse
import requests
import base64
import json
from util import extract_public_key, verify_artifact_signature
from merkle_proof import DefaultHasher, verify_consistency, verify_inclusion, compute_leaf_hash


def get_log_entry(log_index, debug=False):
    """
    Return the single log entry for given log_index.
    """
    # verify that log index value is sane
    try:
        idx = int(log_index)
        if idx < 0:
            raise ValueError()
    except ValueError:
        print("Error: Invalid log index!")
        return

    # use rekor v1 API
    rekor_url = 'https://rekor.sigstore.dev/api/v1/log/entries'
    params = {'logIndex': log_index}
    response = requests.get(rekor_url, params=params)

    # raise error if 4/5xx status code
    response.raise_for_status()

    # get base64 encoded body
    entries = response.json()
    if debug:
        print('Entries:')
        print(json.dumps(entries, indent=4))
        print('\n')
    for entry_id, entry_data in entries.items():
        return entry_data  # only a single entry


def get_certs_from_log_index(log_index, debug=False):
    """
    Get the signature and certificate for given log_index.
    """
    # grab log entry for requested log_index
    log_entry = get_log_entry(log_index, debug)

    # extract base64 encoded body
    body = log_entry['body']
    body_decoded = base64.b64decode(body).decode('utf-8')
    body_json = json.loads(body_decoded)

    # extract out signature and certificate
    spec_data = body_json['spec']
    signature_data = spec_data['signature']
    signature_raw = signature_data['content']
    cert_raw = signature_data['publicKey']['content']

    # decode the raw signature and certificate
    signature = base64.b64decode(signature_raw)
    cert = base64.b64decode(cert_raw)

    return signature, cert


def get_verification_proof(log_index, debug=False):
    """
    Get verification proof key/value pairs for given log_index.
    """
    # grab log entry for requested log_index
    log_entry = get_log_entry(log_index, debug)

    # extract the inclusionProof
    verification = log_entry['verification']
    inclusion_proof = verification['inclusionProof']
 
    # keep track of all keys from inclusionProof
    proof = {}

    # extract appropriate inclusion proof keys
    proof['index'] = inclusion_proof['logIndex']
    proof['tree_size'] = inclusion_proof['treeSize']
    proof['leaf_hash'] = compute_leaf_hash(log_entry['body'])
    proof['hashes'] = inclusion_proof['hashes']
    proof['root_hash'] = inclusion_proof['rootHash']

    return proof
    

def inclusion(log_index, artifact_filepath, debug=False):
    """
    Verify inclusion of an entry in the transparency log.
    """
    # verify artifact filepath exists
    if not os.path.isfile(artifact_filepath):
        print("Error: Artifact filepath ({artifact_filepath}) does not exist!")
        return

    # get log entry from Rekor
    signature, certificate = get_certs_from_log_index(log_index, debug)

    # get public key extracted from certificate
    public_key = extract_public_key(certificate)

    # verify artifact signature
    verify_artifact_signature(signature, public_key, artifact_filepath)

    # get verification proof key/value pairs
    proof = get_verification_proof(log_index)
    index = proof['index']
    tree_size = proof['tree_size']
    leaf_hash = proof['leaf_hash']
    hashes = proof['hashes']
    root_hash = proof['root_hash']

    # verify inclusion given proof key/value pairs for given log_index
    verify_inclusion(DefaultHasher, index, tree_size, leaf_hash, hashes, root_hash, debug)

    print('Inclusion verification successful.')


def get_latest_checkpoint(debug=False):
    """
    Fetch the latest checkpoint from rekor
    """
    # use rekor v1 API
    rekor_url = 'https://rekor.sigstore.dev/api/v1/log'
    response = requests.get(rekor_url)

    # raise error if 4/5xx status code
    response.raise_for_status()

    # extract checkpoint data
    checkpoint = response.json()

    # if debug is enabled, store it in a file checkpoint.json
    if debug:
        with open("checkpoint.json", "w") as f:
            json.dump(checkpoint, f, indent=4)

    return checkpoint


def get_consistency_proof(tree_id, first_tree_size, last_tree_size):
    """
    Fetch the consistency proof given the tree ID and first to 
    last tree size.
    """
    # ensure sane values for tree sizes
    if first_tree_size < 1 or last_tree_size < first_tree_size:
        print(f'Error: invalid tree sizes given: [{first_tree_size}, {last_tree_size}]')

    # use rektor v1 API
    rekor_url = 'https://rekor.sigstore.dev/api/v1/log/proof'
    params = {
        'firstSize': first_tree_size,
        'lastSize': last_tree_size,
        'treeID': tree_id
    }
    response = requests.get(rekor_url, params=params)

    # raise error if 4/5xx status code
    response.raise_for_status()

    # extract hashes from proof data
    proof = response.json()
    hashes = proof['hashes']

    return hashes


def consistency(prev_checkpoint, debug=False):
    """
    Verify consistency of the transparency log.
    """
    # verify that prev checkpoint is not empty
    keys = ['treeID', 'treeSize', 'rootHash']
    for k in keys:
        if k not in prev_checkpoint:
            print(f'Error missing key of previous checkpoint: {k}')
            return

    # get latest checkpoint data
    latest_checkpoint = get_latest_checkpoint()
    if debug:
        print('Latest checkpoint:')
        print(latest_checkpoint)
        print('\n')

    size1 = prev_checkpoint['treeSize']  # this is the older checkpoint by user
    root1 = prev_checkpoint['rootHash']  # this is the older checkpoint root hash by user

    size2 = latest_checkpoint['treeSize']  # this is the latest checkpoint tree size
    root2 = latest_checkpoint['rootHash']  # this is the latest checkpoint root hash

    if debug:
        print(f'{size1=}')
        print(f'{size2=}')
        print(f'{root1=}')
        print(f'{root2=}')
        print('\n')

    # get the consistency proof
    proof = get_consistency_proof(prev_checkpoint['treeID'], size1, size2)
    if debug:
        print('Proof:')
        print(proof)
        print('\n')

    # verify the checkpoint input by the user is consistent 
    # with the latest fetched checkpoint
    verify_consistency(DefaultHasher, size1, size2, proof, root1, root2)

    print('Consistency verification successful.')
 

def main():
    debug = False
    parser = argparse.ArgumentParser(description="Rekor Verifier")
    parser.add_argument('-d', '--debug', help='Debug mode',
                        required=False, action='store_true') # Default false
    parser.add_argument('-c', '--checkpoint', help='Obtain latest checkpoint\
                        from Rekor Server public instance',
                        required=False, action='store_true')
    parser.add_argument('--inclusion', help='Verify inclusion of an\
                        entry in the Rekor Transparency Log using log index\
                        and artifact filename.\
                        Usage: --inclusion 126574567',
                        required=False, type=int)
    parser.add_argument('--artifact', help='Artifact filepath for verifying\
                        signature',
                        required=False)
    parser.add_argument('--consistency', help='Verify consistency of a given\
                        checkpoint with the latest checkpoint.',
                        action='store_true')
    parser.add_argument('--tree-id', help='Tree ID for consistency proof',
                        required=False)
    parser.add_argument('--tree-size', help='Tree size for consistency proof',
                        required=False, type=int)
    parser.add_argument('--root-hash', help='Root hash for consistency proof',
                        required=False)
    args = parser.parse_args()
    if args.debug:
        debug = True
        print("enabled debug mode")
    if args.checkpoint:
        # get and print latest checkpoint from server
        # if debug is enabled, store it in a file checkpoint.json
        checkpoint = get_latest_checkpoint(debug)
        print(json.dumps(checkpoint, indent=4))
    if args.inclusion:
        inclusion(args.inclusion, args.artifact, debug)
    if args.consistency:
        if not args.tree_id:
            print("please specify tree id for prev checkpoint")
            return
        if not args.tree_size:
            print("please specify tree size for prev checkpoint")
            return
        if not args.root_hash:
            print("please specify root hash for prev checkpoint")
            return

        prev_checkpoint = {}
        prev_checkpoint["treeID"] = args.tree_id
        prev_checkpoint["treeSize"] = args.tree_size
        prev_checkpoint["rootHash"] = args.root_hash

        consistency(prev_checkpoint, debug)

if __name__ == "__main__":
    main()
