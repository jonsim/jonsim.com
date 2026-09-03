"""The cook-render command-line application."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from cook_render.render import (
    render_index,
    render_index_by_ingredient,
    render_recipe,
)


def load_recipe(cook_path: Path) -> dict:
    """Run `cook recipe -f json` on a .cook file and parse the JSON output."""
    result = subprocess.run(
        ['cook', 'recipe', '-f', 'json', str(cook_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def main(argv=None):
    """Find all .cook files in base-path and convert them to HTML in output-dir."""
    parser = argparse.ArgumentParser(description='Render cooklang recipes as HTML.')
    parser.add_argument(
        '-b',
        '--base-path',
        type=Path,
        default=Path('.'),
        help='Root directory containing your recipe files',
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        type=Path,
        default=Path('site'),
        help='Path to output the recipe site to',
    )
    args = parser.parse_args(argv)

    base_path = args.base_path
    output_dir = args.output_dir

    if not base_path.exists() or not base_path.is_dir():
        parser.error(f"Base path '{base_path}' is not a directory")

    resolved_output = output_dir.resolve()
    cook_files = [
        p
        for p in base_path.rglob('*.cook')
        if not (
            resolved_output.exists() and p.resolve().is_relative_to(resolved_output)
        )
    ]
    cook_files.sort()

    recipe_items = []
    has_errors = False
    for cook_file in cook_files:
        try:
            recipe = load_recipe(cook_file)
        except FileNotFoundError:
            print(
                "Error: 'cook' command not found. Please install CookCLI.",
                file=sys.stderr,
            )
            return 1
        except subprocess.CalledProcessError as err:
            print(
                f"Error parsing '{cook_file}': {err.stderr.strip()}",
                file=sys.stderr,
            )
            has_errors = True
            continue
        except json.JSONDecodeError as err:
            print(
                f"Error reading JSON from '{cook_file}': {err}",
                file=sys.stderr,
            )
            has_errors = True
            continue

        relative_path = cook_file.relative_to(base_path)
        depth = len(relative_path.parent.parts)
        root_path = '../' * depth
        html_content = render_recipe(recipe, root_path=root_path)
        target_path = output_dir / relative_path.with_suffix('.html')
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(html_content, encoding='utf-8')

        recipe_items.append(
            {
                'recipe': recipe,
                'href': target_path.relative_to(output_dir).as_posix(),
                'relative_path': relative_path,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    index_html = render_index(recipe_items)
    (output_dir / 'index.html').write_text(index_html, encoding='utf-8')

    ingredient_index_html = render_index_by_ingredient(recipe_items)
    (output_dir / 'index_by_ingredient.html').write_text(
        ingredient_index_html, encoding='utf-8'
    )

    return 1 if has_errors else 0
