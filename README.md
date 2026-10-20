# Software Supply Chain Security - Rekor Monitor

A Python-based utility built to monitor and verify software supply chain artifacts using a Rekor log / transparency ledger framework.

## Usage

```bash
usage: main.py [-h] [-d] [-c] [--inclusion INCLUSION] [--artifact ARTIFACT] [--consistency] [--tree-id TREE_ID] [--tree-size TREE_SIZE] [--root-hash ROOT_HASH]
```

#### Examples:

To sign an artifact using cosign.

```
cosign sign-blob artifact.md --bundle artifact.bundle
```

To verify that your log index is present in Rekor.

```
main.py --inclusion \<logIndex> --artifact artifact.md
```

To fetch and store the latest checkpoint.

```
main.py -c
```

To verify the consistency of the log between two stages.

```
main.py --consistency --tree-id <> --tree-size <> --root-hash <>
```

## Installation

Ensure you have Python 3.11+ installed alongside Poetry:

```bash
python --version
poetry --version
```

Clone the repository, navigate to the directory, and setup a virtual environment:

```bash
git clone https://github.com/chell22m/supply-chain-security-a1
cd supply-chain-security-a1
python3 -m venv .venv
source .venv/bin/activate
pip install requests cryptography
```

or with poetry:

```bash
git clone https://github.com/chell22m/supply-chain-security-a1
cd supply-chain-security-a1
poetry install
```

## Development

Linting, typing, and security policies are enforced across the codebase using the following tools: ruff, mypy, and bandit.

```bash
# format
poetry run ruff format --check

# linter
poetry run ruff check

# mypy
poetry run mypy main.py merkle_proof.py util.py 

# bandit
poetry run bandit -c pyproject.toml -r . 
```

[Contribution guidelines for this project](CONTRIBUTING.md)

