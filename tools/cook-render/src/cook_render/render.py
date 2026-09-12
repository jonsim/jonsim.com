"""Turn CookCLI's JSON recipe output into HTML pages."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from jinja2 import Environment, PackageLoader, select_autoescape

TEMPLATES = Environment(
    loader=PackageLoader('cook_render', 'templates'),
    autoescape=select_autoescape(['html']),
    keep_trailing_newline=True,
)

COURSE_ORDER = [
    'Breakfast',
    'Brunch',
    'Lunch',
    'Dinner',
    'Sides',
    'Starters',
    'Dessert',
    'Baking',
    'Snacks',
    'Drinks',
]

KNOWN_COURSES = {
    'breakfast': 'Breakfast',
    'brunch': 'Brunch',
    'lunch': 'Lunch',
    'dinner': 'Dinner',
    'main': 'Dinner',
    'mains': 'Dinner',
    'side': 'Sides',
    'sides': 'Sides',
    'dessert': 'Dessert',
    'desserts': 'Dessert',
    'starter': 'Starters',
    'starters': 'Starters',
    'baking': 'Baking',
    'snack': 'Snacks',
    'snacks': 'Snacks',
    'drink': 'Drinks',
    'drinks': 'Drinks',
}


class TimeDuration:
    @staticmethod
    def _parse(s: str) -> int:
        """Parse strings like '15 minutes', '1 hour', '1 hour 30 minutes' into total minutes."""
        hours = re.search(r'(\d+)\s*h', s)
        minutes = re.search(r'(\d+)\s*m', s)
        total = 0
        matched = False
        if hours:
            matched = True
            total += int(hours.group(1)) * 60
        if minutes:
            matched = True
            total += int(minutes.group(1))
        if not matched:
            raise ValueError(f'{s!r} is not a valid TimeDuration')
        return total

    def __init__(self, formatted_or_minutes: int | str):
        if isinstance(formatted_or_minutes, int):
            self.total_minutes = formatted_or_minutes
        elif isinstance(formatted_or_minutes, str):
            self.total_minutes = self._parse(formatted_or_minutes)
        else:
            raise TypeError('formatted_or_minutes must be an int or str')

    @property
    def formatted(self) -> str:
        hours, minutes = divmod(self.total_minutes, 60)
        parts = []
        if hours:
            parts.append(f'{hours} hour' + ('s' if hours != 1 else ''))
        if minutes or not parts:
            parts.append(f'{minutes} minute' + ('s' if minutes != 1 else ''))
        return ' '.join(parts)

    def __bool__(self) -> bool:
        return self.total_minutes > 0

    def __add__(self, other: 'TimeDuration') -> 'TimeDuration':
        return self.__class__(self.total_minutes + other.total_minutes)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.total_minutes < other.total_minutes

    def __le__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.total_minutes <= other.total_minutes

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.total_minutes > other.total_minutes

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.total_minutes >= other.total_minutes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.total_minutes == other.total_minutes

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.total_minutes != other.total_minutes

    def __hash__(self) -> int:
        return hash(self.total_minutes)

    def __str__(self) -> str:
        return self.formatted


@dataclass
class Metadata:
    # Based on https://cooklang.org/docs/conventions/#canonical-metadata

    source: str
    author: str
    url: str
    servings: str
    course: str
    locale: str
    total_time: TimeDuration
    prep_time: TimeDuration
    cook_time: TimeDuration
    difficulty: str
    cuisine: str
    diets: list[str]
    tags: list[str]
    images: list[str]
    title: str
    description: str
    other: dict[str, str]

    def all_fields(self) -> Iterator[tuple[str, str]]:
        if self.title:
            yield ('title', self.title)
        if self.description:
            yield ('description', self.description)
        if self.servings:
            yield ('servings', str(self.servings))
        if self.course:
            yield ('course', self.course)
        if self.locale:
            yield ('locale', self.locale)
        if self.total_time is not None:
            yield ('total_time', self.total_time.formatted)
        if self.prep_time is not None:
            yield ('prep_time', self.prep_time.formatted)
        if self.cook_time is not None:
            yield ('cook_time', self.cook_time.formatted)
        if self.difficulty:
            yield ('difficulty', self.difficulty)
        if self.cuisine:
            yield ('cuisine', self.cuisine)
        if self.diets:
            yield ('diets', ', '.join(self.diets))
        if self.tags:
            yield ('tags', ', '.join(self.tags))
        if self.images:
            yield ('images', ', '.join(self.images))
        if self.other:
            yield from self.other.items()

    @classmethod
    def from_recipe(cls, recipe: dict) -> 'Metadata':
        def _get_metadata_field(*field_names):
            for field in field_names:
                value = metadata.get(field)
                if value is None:
                    continue
                else:
                    return value
            return None

        def _get_str_metadata_field(*field_names):
            value = _get_metadata_field(*field_names)
            if not value:
                return None
            elif isinstance(value, str):
                return value.strip()
            else:
                raise TypeError(f'metadata {field_names!r}: {value!r} must be a string')

        def _get_int_metadata_field(*field_names):
            value = _get_metadata_field(*field_names)
            if not value:
                return None
            elif isinstance(value, int):
                return value
            elif isinstance(value, str):
                return int(value.split(' ', 1)[0])
            else:
                raise TypeError(f'metadata {field_names!r}: {value!r} must be an int')

        def _get_list_metadata_field(*field_names):
            value = _get_metadata_field(*field_names)
            if not value:
                return None
            elif isinstance(value, str):
                return [item.strip() for item in value.split(',')]
            elif isinstance(value, list):
                return value
            raise TypeError(
                f'metadata {field_names!r}: {value!r} must be a string or list'
            )

        def _get_time_metadata_field(*field_names):
            value = _get_metadata_field(*field_names)
            if value is None:
                return None
            return TimeDuration(value)

        # Extract metadata map.
        metadata = recipe.get('metadata', recipe.get('raw_metadata', {}))
        metadata = metadata.get('map', metadata)

        # Parse metadata fields.
        source = _get_str_metadata_field('source', 'source.name')
        author = _get_str_metadata_field('author', 'source.author')
        url = _get_str_metadata_field('url', 'source.url')
        servings = _get_int_metadata_field('servings', 'serves', 'yield')
        course = _get_str_metadata_field('course', 'category')
        locale = _get_str_metadata_field('locale')
        total_time = _get_time_metadata_field(
            'time required', 'time', 'duration', 'time.total'
        )
        prep_time = _get_time_metadata_field('prep time', 'time.prep')
        cook_time = _get_time_metadata_field('cook time', 'time.cook')
        difficulty = _get_str_metadata_field('difficulty')
        cuisine = _get_str_metadata_field('cuisine')
        diets = _get_list_metadata_field('diet')
        tags = _get_list_metadata_field('tags')
        images = _get_list_metadata_field('image', 'images', 'picture', 'pictures')
        title = _get_str_metadata_field('title')
        description = _get_str_metadata_field('introduction', 'description')

        # Get other metadata fields.
        other = {}
        for field in metadata:
            if field not in (
                'source',
                'source.name',
                'author',
                'source.author',
                'url',
                'source.url',
                'servings',
                'serves',
                'yield',
                'course',
                'category',
                'locale',
                'time required',
                'time',
                'duration',
                'time.total',
                'prep time',
                'time.prep',
                'cook time',
                'time.cook',
                'difficulty',
                'cuisine',
                'diet',
                'tags',
                'image',
                'images',
                'picture',
                'pictures',
                'title',
                'introduction',
                'description',
            ):
                value = metadata[field]
                if value is None:
                    continue
                elif isinstance(value, str):
                    other[field] = value.strip()
                elif isinstance(value, (list, tuple)):
                    other[field] = ', '.join(str(item).strip() for item in value)
                else:
                    other[field] = str(value)

        # Post-process fields.
        if prep_time is not None and cook_time is not None:
            total_time = prep_time + cook_time

        return cls(
            source=source,
            author=author,
            url=url,
            servings=servings,
            course=course,
            locale=locale,
            total_time=total_time,
            prep_time=prep_time,
            cook_time=cook_time,
            difficulty=difficulty,
            cuisine=cuisine,
            diets=diets,
            tags=tags,
            images=images,
            title=title,
            description=description,
            other=other,
        )


def _format_number(number):
    """Format Cooklang's regular and fractional JSON number variants."""
    if not isinstance(number, dict):
        return str(number)
    kind = number.get('type')
    value = number.get('value')
    if kind == 'regular':
        return f'{value:.3f}'.rstrip('0').rstrip('.')
    if kind == 'fraction':
        whole = value.get('whole', 0)
        numerator = value.get('num', 0)
        denominator = value.get('den', 1)
        if whole and numerator:
            return f'{whole} {numerator}/{denominator}'
        if whole:
            return str(whole)
        return f'{numerator}/{denominator}'
    return str(value)


def _format_quantity(quantity):
    """Format a serialised Cooklang quantity for display."""
    if not quantity:
        return ''
    value = quantity.get('value', {})
    kind = value.get('type')
    if kind == 'number':
        amount = _format_number(value.get('value'))
    elif kind == 'range':
        bounds = value.get('value', {})
        amount = (
            f'{_format_number(bounds.get("start"))}-{_format_number(bounds.get("end"))}'
        )
    else:
        amount = str(value.get('value', ''))
    unit = quantity.get('unit')
    return f'{amount} {unit}' if unit else amount


def _quantity_number(quantity):
    """Return an ordinary number when a quantity can be added safely."""
    if not quantity:
        return None
    value = quantity.get('value', {})
    number = value.get('value', {})
    if value.get('type') != 'number' or number.get('type') != 'regular':
        return None
    return number.get('value')


def _ingredient_relation(ingredient):
    relation = ingredient.get('relation', {})
    return relation.get('relation', relation)


def _is_definition(component, *, ingredient=False):
    relation = (
        _ingredient_relation(component) if ingredient else component.get('relation', {})
    )
    return relation.get('type', 'definition') == 'definition'


def _grouped_quantity(ingredient, ingredients):
    """Combine an ingredient's own quantity with quantities on references."""
    relation = _ingredient_relation(ingredient)
    quantities = [ingredient.get('quantity')]
    quantities.extend(
        ingredients[index].get('quantity')
        for index in relation.get('referenced_from', [])
    )
    quantities = [quantity for quantity in quantities if quantity]
    if not quantities:
        return ''

    # Cooklang can convert compatible units too. We only add quantities which
    # already use the same unit; anything else remains readable.
    units = {quantity.get('unit') for quantity in quantities}
    numbers = [_quantity_number(quantity) for quantity in quantities]
    if len(units) == 1 and all(number is not None for number in numbers):
        quantity = dict(quantities[0])
        quantity['value'] = {
            'type': 'number',
            'value': {'type': 'regular', 'value': sum(numbers)},
        }
        return _format_quantity(quantity)
    return ', '.join(_format_quantity(quantity) for quantity in quantities)


def _requirements(recipe):
    ingredients = recipe.get('ingredients', [])
    ingredient_rows = [
        {
            'name': (ingredient.get('alias') or ingredient.get('name', '')).title(),
            'quantity': _grouped_quantity(ingredient, ingredients),
        }
        for ingredient in ingredients
        if _is_definition(ingredient, ingredient=True)
    ]
    cookware_rows = [
        {
            'name': (cookware.get('alias') or cookware.get('name', '')).title(),
            'quantity': _format_quantity(cookware.get('quantity')),
        }
        for cookware in recipe.get('cookware', [])
        if _is_definition(cookware)
    ]
    return ingredient_rows, cookware_rows


def _prepare_step_item(recipe, item):
    """Resolve one indexed Cooklang step item for the template."""
    kind = item.get('type')
    if kind == 'text':
        return {'type': kind, 'value': item.get('value', '')}
    if kind == 'ingredient':
        ingredient = recipe['ingredients'][item['index']]
        return {
            'type': kind,
            'name': ingredient.get('alias') or ingredient.get('name', ''),
            'quantity': _format_quantity(ingredient.get('quantity')),
        }
    if kind == 'cookware':
        cookware = recipe['cookware'][item['index']]
        return {
            'type': kind,
            'name': cookware.get('alias') or cookware.get('name', ''),
            'quantity': _format_quantity(cookware.get('quantity')),
        }
    if kind == 'timer':
        timer = recipe['timers'][item['index']]
        parts = [timer.get('name'), _format_quantity(timer.get('quantity'))]
        return {
            'type': kind,
            'value': ' '.join(str(part) for part in parts if part),
        }
    if kind == 'inlineQuantity':
        quantity = recipe['inline_quantities'][item['index']]
        return {'type': kind, 'value': _format_quantity(quantity)}
    return {'type': 'unknown'}


def _method_and_notes(recipe):
    method_sections = []
    notes = []
    for section in recipe.get('sections', []):
        blocks = []
        for content in section.get('content', []):
            if content.get('type') == 'step':
                step = content.get('value', {})
                items = [
                    _prepare_step_item(recipe, item) for item in step.get('items', [])
                ]
                if blocks and blocks[-1]['type'] == 'steps':
                    blocks[-1]['steps'].append(items)
                else:
                    blocks.append({'type': 'steps', 'steps': [items]})
            elif content.get('type') == 'text':
                value = content.get('value', '').strip()
                if value.lower().startswith('note'):
                    notes.append(value[4:].lstrip(' -:.\t').strip())
                else:
                    blocks.append({'type': 'text', 'value': value})
        method_sections.append({'name': section.get('name'), 'blocks': blocks})
    return method_sections, notes


def _root_prefix(root_path: str):
    if root_path and not root_path.endswith('/'):
        root_path += '/'
    return root_path


def render_recipe(recipe, root_path: str):
    """Render one CookCLI JSON recipe as a complete HTML document."""
    metadata = Metadata.from_recipe(recipe)
    ingredients, cookware = _requirements(recipe)
    method_sections, notes = _method_and_notes(recipe)
    recipe_root = _root_prefix(root_path)
    return TEMPLATES.get_template('recipe.html').render(
        title=metadata.title or 'Recipe',
        description=metadata.description,
        image=metadata.images[0] if metadata.images else None,
        metadata=metadata,
        ingredients=ingredients,
        cookware=cookware,
        method_sections=method_sections,
        notes=notes,
        recipe_root=recipe_root,
    )


def _recipe_group(item):
    # Prefer getting the group from the course data.
    metadata = Metadata.from_recipe(item.get('recipe', {}))
    if metadata.course:
        return metadata.course.title()
    # Otherwise, fall back to parent directory name.
    relative_path = item.get('relative_path')
    if relative_path and str(relative_path.parent) != '.':
        parent_name = relative_path.parent.parts[0]
        return KNOWN_COURSES.get(
            parent_name.lower(), parent_name.replace('-', ' ').replace('_', ' ').title()
        )
    return 'Recipes'


def _group_sort_key(name):
    if name in COURSE_ORDER:
        return (0, COURSE_ORDER.index(name))
    if name in {'Recipes', 'Other'}:
        return (2, name)
    return (1, name)


def render_index(recipe_items: list[dict]) -> str:
    """Render an index page listing all recipes grouped by course."""
    grouped = {}
    for item in recipe_items:
        grouped.setdefault(_recipe_group(item), []).append(item)
    groups = []
    for name in sorted(grouped, key=_group_sort_key):
        items = sorted(
            grouped[name],
            key=lambda item: Metadata.from_recipe(item.get('recipe', {})).title.lower(),
        )
        recipes = []
        for item in items:
            metadata = Metadata.from_recipe(item.get('recipe', {}))
            recipes.append(
                {
                    'title': metadata.title or item.get('href', 'Recipe'),
                    'description': metadata.description,
                    'href': item.get('href', '#'),
                    'time': str(metadata.total_time) if metadata.total_time else None,
                    'servings': f'serves {metadata.servings}'
                    if metadata.servings
                    else None,
                }
            )
        groups.append(
            {
                'name': name,
                'id': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
                'recipes': recipes,
            }
        )
    return TEMPLATES.get_template('index.html').render(groups=groups)


def render_index_by_ingredient(recipe_items: list[dict]) -> str:
    """Render an index page listing all recipes grouped by ingredient."""
    ingredient_map = {}
    for item in recipe_items:
        metadata = Metadata.from_recipe(item.get('recipe', {}))
        recipe_title = metadata.title or item.get('href', 'Recipe')
        seen_for_recipe = set()
        for ingredient in item.get('recipe', {}).get('ingredients', []):
            name = (ingredient.get('name') or ingredient.get('alias') or '').strip()
            normalized = name.lower()
            if not name or normalized in seen_for_recipe:
                continue
            seen_for_recipe.add(normalized)
            entry = ingredient_map.setdefault(
                normalized, {'term': name.capitalize(), 'recipes': []}
            )
            entry['recipes'].append(
                {'title': recipe_title, 'href': item.get('href', '#')}
            )
    ingredients = sorted(ingredient_map.values(), key=lambda item: item['term'].lower())
    for ingredient in ingredients:
        ingredient['recipes'].sort(key=lambda recipe: recipe['title'].lower())
    return TEMPLATES.get_template('index_by_ingredient.html').render(
        ingredients=ingredients
    )
