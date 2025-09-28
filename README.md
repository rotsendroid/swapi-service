
# Tests
## Single test
pytest tests/unit/core/populatedb/test_service.py::TestPopulateDBService::test_map_input_to_model_basic

## All tests in a file
  pytest tests/unit/utils/test_url_helpers.py

## All unit tests
  pytest tests/unit/

## All tests
  pytest


# Development setup

pyenv local 3.13

uv init

pre-commit install

pre-commit run -a

uv sync --extra dev

uv run fastapi dev

main.py --reload
