"""The blog-render command-line application."""

import argparse
import shutil
from html.parser import HTMLParser
from importlib import resources
from pathlib import Path

from blog_render.render import (
    render_blog,
    render_index,
)


def deploy_images(
    md_path: Path,
    base_path: Path,
    output_dir: Path,
    html_content: str,
    metadata: object,
) -> None:
    """Download or copy images into the output directory, so the HTML template
    can find it.

    The resultant image ends up in same output dir the HTML file will end up in,
    named identically save for the extension.
    """

    class ImageExtractor(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                images.append(dict(attrs)['src'])

    images = []
    if metadata.image:
        images.append(metadata.image)

    parser = ImageExtractor()
    parser.feed(html_content)

    for image in images:
        image_path = md_path.parent / image
        output_path = output_dir / image_path.relative_to(base_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if image_path.is_file():
            shutil.copy2(image_path, output_path)
        else:
            print(f'WARNING: image {image_path} not found for post {md_path}')


def main(argv=None):
    """Find all .md files in base-path and convert them to HTML in output-dir."""
    parser = argparse.ArgumentParser(description='Render markdown as HTML.')
    parser.add_argument(
        '-b',
        '--base-path',
        type=Path,
        default=Path('.'),
        help='Root directory containing your markdown files',
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        type=Path,
        default=Path('site'),
        help='Path to output the blog site to',
    )
    args = parser.parse_args(argv)

    base_path = args.base_path
    output_dir = args.output_dir

    if not base_path.exists() or not base_path.is_dir():
        parser.error(f"Base path '{base_path}' is not a directory")

    resolved_output = output_dir.resolve()
    blog_files = [
        p
        for p in base_path.rglob('*.md')
        if not (
            resolved_output.exists() and p.resolve().is_relative_to(resolved_output)
        )
    ]
    blog_files.sort()

    blog_items = []
    has_errors = False
    for md_file in blog_files:
        relative_path = md_file.relative_to(base_path)
        depth = len(relative_path.parent.parts)
        root_path = '../' * depth

        target_path = output_dir / relative_path.with_suffix('.html')
        target_path.parent.mkdir(parents=True, exist_ok=True)

        html_content, metadata = render_blog(md_file, root_path)
        target_path.write_text(html_content, encoding='utf-8')

        deploy_images(md_file, base_path, output_dir, html_content, metadata)

        blog_items.append(
            {
                'blog': html_content,
                'metadata': metadata,
                'href': target_path.relative_to(output_dir).as_posix(),
                'relative_path': relative_path,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    static_dir = resources.files('blog_render').joinpath('static')

    # Output the recipe stylesheet.
    content = static_dir.joinpath('blog_style.css').read_text(encoding='utf-8')
    (output_dir / 'blog_style.css').write_text(content, encoding='utf-8')

    # Output the index page.
    index_html = render_index(blog_items)
    (output_dir / 'index.html').write_text(index_html, encoding='utf-8')

    # TODO: more index pages.
    # ingredient_index_html = render_index_by_ingredient(blog_items)
    # (output_dir / 'index_by_ingredient.html').write_text(
    #     ingredient_index_html, encoding='utf-8'
    # )

    return 1 if has_errors else 0
