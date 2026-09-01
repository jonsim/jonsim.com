# cook-render

A simple Python command-line application to generate a static HTML recipe from a cooklang `.cook` file.

## Usage

Install [CookCLI](https://github.com/cooklang/CookCLI).

Pipe the output of `cook recipe` into `cook-render`:

```sh
cook recipe -f json tests/examples/pancakes.cook | uv run cook-render -o pancakes.html
```

The `-o` argument sets the output file. Defaults to `-`, meaning standard output.

The `-i` argument sets the input file. Defaults to `-`, meaning standard input.


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
