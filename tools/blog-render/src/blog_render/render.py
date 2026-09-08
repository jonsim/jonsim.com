"""Turn Markdown blog posts into HTML pages."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import mistune
from jinja2 import Environment, PackageLoader, select_autoescape

TEMPLATES = Environment(
    loader=PackageLoader('blog_render', 'templates'),
    autoescape=select_autoescape(['html']),
    keep_trailing_newline=True,
)


@dataclass
class Metadata:
    title: str
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


def parse_metadata(text: str) -> tuple[str, Metadata]:
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return text, Metadata('Post', None, None, None, [], {})

    metadata = {}
    end_index = len(lines)
    for i, line in enumerate(lines[1:], start=1):
        if line == '---':
            end_index = i
            break
        key, value = line.split(':', 1)
        metadata[key.strip()] = value.strip()

    title = metadata.pop('title', 'Post')
    date_str = metadata.pop('date', None)
    date_obj = date.fromisoformat(date_str) if date_str else None
    description = metadata.pop('description', None)
    image = metadata.pop('image', None)
    tags_str = metadata.pop('tags', None)
    tags = [t.lower().strip() for t in tags_str.split(',')] if tags_str else []
    remainder = '\n'.join(lines[end_index + 1 :])
    return remainder, Metadata(title, date_obj, description, image, tags, metadata)


def render_content(markdown: str) -> str:
    return mistune.html(markdown)


def render_blog(md_path: Path) -> tuple[str, Metadata]:
    with open(md_path) as md_file:
        text = md_file.read()
        markdown, metadata = parse_metadata(text)
        content = render_content(markdown)

    return TEMPLATES.get_template('blog.html').render(
        metadata=metadata,
        content=content,
        blog_root='',
        site_root='../',
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
