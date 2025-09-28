
# Development Environment setup

```bash
pyenv local 3.13

uv init

pre-commit install

pre-commit run -a

uv sync --extra dev

docker compose -f docker-compose.dev.yml up --build

uv run fastapi dev main.py --reload
```


# Tests commands

## All tests
```bash
pytest
```

## All unit tests
```bash
pytest tests/unit/
```

## All tests in a file
```bash
pytest tests/unit/utils/test_url_helpers.py
```

## Single test
```bash
pytest tests/unit/core/populatedb/test_service.py::TestPopulateDBService::test_map_input_to_model_basic
```

## Generate MD coverage report
```bash
pytest --cov-report markdown
```
