# cook-render

A simple Python command-line application to generate a static HTML recipe site from cooklang `.cook` files.

## Usage

Install [CookCLI](https://github.com/cooklang/CookCLI).

Run `cook-render` pointing to your recipes:

```sh
uv run cook-render --base-path recipes --output-dir site
```

The `--base-path` / `-b` argument specifies the root directory containing your recipe files (defaults to `.`).

The `--output-dir` / `-o` argument specifies the path to output the recipe site to (defaults to `site`).


## Contributing

### Set up the project

This project uses [uv](https://docs.astral.sh/uv/) for package management and dependency resolution.

Install the application and its development dependencies:

```sh
uv sync --group dev
```

Install the pre-commit hooks:

```sh
uv run pre-commit install
```

Run the command:

```sh
uv run cook-render
```

### Run the tests

The unit tests use Python's standard `unittest` framework:

```sh
uv run python -m unittest discover -s tests
```

Run the same tests with coverage and print the missing lines:

```sh
uv run coverage run -m unittest discover -s tests
uv run coverage report
```

You can also manually run the commit checks at any time:

```sh
uv run pre-commit run --all-files
```
