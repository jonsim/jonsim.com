"""Turn Markdown blog posts into HTML pages."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import mdtex2html
from jinja2 import Environment, PackageLoader, select_autoescape

TEMPLATES = Environment(
    loader=PackageLoader('blog_render', 'templates'),
    autoescape=select_autoescape(['html']),
    keep_trailing_newline=True,
)


@dataclass
class Metadata:
    title: str | None
    date: date | None
    description: str | None
    image: str | None
    tags: list[str]
    other: dict[str, str]

    def all_fields(self) -> Iterator[tuple[str, str]]:
        yield ('title', self.title)
        if self.date:
            yield ('date', self.date.strftime('%Y-%m-%d'))
        if self.description:
            yield ('description', self.description)
        if self.image:
            yield ('image', self.image)
        if self.tags:
            yield ('tags', ', '.join(self.tags))
        if self.other:
            yield from self.other.items()

    def __bool__(self):
        return bool(self.title) and bool(self.date)


def parse_metadata(text: str) -> tuple[str, Metadata]:
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return text, Metadata(None, None, None, None, None, None)

    metadata = {}
    end_index = len(lines)
    for i, line in enumerate(lines[1:], start=1):
        if line == '---':
            end_index = i
            break
        key, value = line.split(':', 1)
        metadata[key.strip()] = value.strip()

    title = metadata.pop('title', None)
    date_str = metadata.pop('date', None)
    date_obj = date.fromisoformat(date_str) if date_str else None
    description = metadata.pop('description', None)
    image = metadata.pop('image', None)
    tags_str = metadata.pop('tags', None)
    tags = [t.lower().strip() for t in tags_str.split(',')] if tags_str else []
    remainder = '\n'.join(lines[end_index + 1 :])
    return remainder, Metadata(title, date_obj, description, image, tags, metadata)


def _root_prefix(root_path: str):
    if root_path and not root_path.endswith('/'):
        root_path += '/'
    return root_path


def render_content(markdown: str) -> str:
    return mdtex2html.convert(markdown, extensions=['tables', 'fenced_code', 'toc'])


def render_blog(md_path: Path, root_path: str) -> tuple[str, Metadata]:
    with open(md_path) as md_file:
        text = md_file.read()
        markdown, metadata = parse_metadata(text)
        assert metadata, f'{md_path} contains no metadata'
        content = render_content(markdown)

    blog_root = _root_prefix(root_path)
    return TEMPLATES.get_template('blog.html').render(
        metadata=metadata,
        content=content,
        blog_root=blog_root,
    ), metadata


def render_index(blog_items: list[dict]) -> str:
    """Render an index page listing all blogs."""

    # Sort by date, descending (newest first)
    blog_items = sorted(
        blog_items, key=lambda post: post['metadata'].date, reverse=True
    )

    posts = []
    for post in blog_items:
        posts.append(
            {
                'href': post['href'],
                'title': post['metadata'].title,
                'description': post['metadata'].description,
                'date': post['metadata'].date,
                'tags': post['metadata'].tags,
            }
        )

    return TEMPLATES.get_template('index.html').render(
        posts=posts,
        blog_root='',
        site_root='../',
    )
