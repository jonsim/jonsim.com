"""Turn Markdown blog posts into HTML pages."""

from pathlib import Path

import mistletoe


class Metadata:
    def __init__(self, title: str, description: str | None):
        self.title = title
        self.description = description


def render_blog(md_path: Path):
    with open(md_path) as md_file:
        html_content = mistletoe.markdown(md_file)
    return html_content


def render_index(blog_posts: list[dict], title: str = 'jonsim') -> str:
    """Render an index page listing all recipes grouped by course."""
    return 'todo'
