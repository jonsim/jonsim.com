# cook-render

A simple Python command-line application to generate HTML recipe files from cooklang `.cook` files.

## Set up the project

This project uses [uv](https://docs.astral.sh/uv/) for package management and dependency resolution.

Install the application and its development dependencies:

```console
uv sync --group dev
```

Run the command:

```console
uv run cook-render
```

## Run the tests

The unit tests use Python's standard `unittest` framework:

```console
uv run python -m unittest discover -s tests
```

Run the same tests with coverage and print the missing lines:

```console
uv run coverage run -m unittest discover -s tests
uv run coverage report
```

## Run the checks

Install the Git hook once after cloning the project:

```console
uv run pre-commit install
```

Run every check over the repository whenever needed:

```console
uv run pre-commit run --all-files
```
