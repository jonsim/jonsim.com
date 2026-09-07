"""The cook-render command-line application."""

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from importlib import resources
from pathlib import Path

from cook_render.render import (
    render_index,
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


def deploy_image(recipe, base_path: Path, cook_path: Path, output_dir: Path) -> None:
    """Download or copy images into the output directory, fixing up the metadata
    so the HTML template can find it.

    The resultant image ends up in same output dir the HTML file will end up in,
    named identically save for the extension.
    """

    def is_url(maybe_url: str) -> bool:
        return maybe_url.startswith('http://') or maybe_url.startswith('https://')

    metadata = recipe.get('metadata', recipe.get('raw_metadata', {}))
    metadata = metadata.get('map', metadata)
    image = metadata.get('image') or metadata.get('photo')
    if not image:
        return

    image_extension = image.rsplit('.', 1)[1]
    output_path = output_dir / (cook_path.with_suffix(f'.{image_extension}'))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if is_url(image):
        req = urllib.request.Request(
            image,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            },
        )
        with (
            urllib.request.urlopen(req) as response,
            open(output_path, 'wb') as out_file,
        ):
            out_file.write(response.read())
        pass
    else:
        image_path = base_path / image
        if image_path.is_file():
            shutil.copy2(image_path, output_path)
        else:
            print(f'WARNING: image {image_path} not found for recipe {cook_path}')
    metadata['image'] = output_path.name


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
        # depth = len(relative_path.parent.parts)
        # root_path = '../' * depth
        root_path = '../'

        deploy_image(recipe, base_path, relative_path, output_dir)

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
    static_dir = resources.files('cook_render').joinpath('static')

    # Output the recipe stylesheet.
    content = static_dir.joinpath('recipe_style.css').read_text(encoding='utf-8')
    (output_dir / 'recipe_style.css').write_text(content, encoding='utf-8')

    # Output the index page.
    index_html = render_index(recipe_items)
    (output_dir / 'index.html').write_text(index_html, encoding='utf-8')

    # TODO: more index pages.
    # ingredient_index_html = render_index_by_ingredient(recipe_items)
    # (output_dir / 'index_by_ingredient.html').write_text(
    #     ingredient_index_html, encoding='utf-8'
    # )

    return 1 if has_errors else 0
