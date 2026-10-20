# Contributing to Rekor Monitor

Thank you for helping improve this tool! To ensure a smooth review process, please follow these guidelines when submitting changes.

## Development Workflow

1. **Fork the Repository:** Create your own branch from the `main` branch.
2. **Install Workspace Dependencies:**
   ```bash
   poetry install
   ```
3. **Implement Changes:** Write clean, modular Python code.

## Quality Standards

Before committing your changes or opening a Pull Request, you must run the following checks locally. Code that passes these steps has a much faster path to being merged.

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

## Pull Request Guidelines

* **Keep PRs focused:** Fix one bug or add one feature per PR.
* **Update the README:** If you alter execution commands or add configuration variables, ensure documentation matches.
* **Be responsive:** Engage with the maintainers during code reviews to finalize revisions.

