


# Development setup

pyenv local 3.13
uv init

pre-commit run -a

uv run fastapi dev main.py --reload
