# Backend

This is the FastAPI backend for lyrics thing

## Development

### Install poetry:

Run these commands:
`brew install pipx`
`pipx install poetry`
`pipx ensurepath`

Then stop and restart terminal.

### Install dependencies:

```bash
poetry install
```

#### Run the dev server:

```bash
poetry shell # Switch to the Poetry virtual environment.
python main.py
```

## Set-up

Install our recommended VSCode extensions by running the `show recommended extensions` command.

Then install the pre-commit git hook. First make sure you have run `poetry shell`. Then run `pre-commit install`.
