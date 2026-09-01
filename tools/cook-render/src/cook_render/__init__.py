"""The cook-render command-line application."""

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path

from cook_render.render import render_recipe


@contextmanager
def open_input(path: Path):
    if path == Path('-'):
        yield sys.stdin
    else:
        with open(path, encoding='utf-8') as f:
            yield f


@contextmanager
def open_output(path: Path):
    if path == Path('-'):
        yield sys.stdout
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yield f


def main(argv=None):
    """Read a JSON recipe from stdin and write its HTML page."""
    parser = argparse.ArgumentParser(
        description="Render the JSON output from 'cook recipe -f json' as HTML."
    )
    parser.add_argument(
        '-i',
        '--input',
        type=Path,
        default='-',
        help='JSON file to read, or - to read from stdin. Defaults to stdin.',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        default='-',
        help='HTML file to write, or - to output to stdout. Defaults to stdout.',
    )
    args = parser.parse_args(argv)

    # Open and the input and output files.
    with open_input(args.input) as input, open_output(args.output) as output:
        # Parse the recipe.
        try:
            recipe = json.load(input)
        except json.JSONDecodeError as error:
            parser.error(f'stdin is not valid JSON: {error}')
        if not isinstance(recipe, dict):
            parser.error('stdin must contain one JSON recipe object')

        # Render the recipe.
        output.write(render_recipe(recipe))

    return 0
