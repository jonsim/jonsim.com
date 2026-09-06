"""Turn CookCLI's JSON recipe output into HTML pages."""

import json
import re

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


def _metadata_map(recipe):
    metadata = recipe.get('metadata', recipe.get('raw_metadata', {}))
    return metadata.get('map', metadata)


def _metadata_fields(metadata):
    fields = []
    for key, value in sorted(metadata.items()):
        if key in {'title', 'description', 'image', 'photo'}:
            continue
        label = 'Serves' if key == 'servings' else key.replace('_', ' ').title()
        tags = value if key.lower() == 'tags' and isinstance(value, list) else None
        if tags is not None:
            display_value = None
        elif isinstance(value, list):
            display_value = ', '.join(str(item) for item in value)
        elif isinstance(value, str):
            display_value = value
        else:
            display_value = json.dumps(value, separators=(',', ':'))
        fields.append({'label': label, 'value': display_value, 'tags': tags})
    return fields


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


def _root_prefix(root_path):
    if isinstance(root_path, int):
        return '../' * root_path
    root_prefix = str(root_path)
    if root_prefix and not root_prefix.endswith('/'):
        root_prefix += '/'
    return root_prefix


def render_recipe(recipe, root_path: str | int = ''):
    """Render one CookCLI JSON recipe as a complete HTML document."""
    metadata = _metadata_map(recipe)
    ingredients, cookware = _requirements(recipe)
    method_sections, notes = _method_and_notes(recipe)
    recipe_root = _root_prefix(root_path)
    return TEMPLATES.get_template('recipe.html').render(
        title=metadata.get('title') or 'Recipe',
        description=metadata.get('description'),
        image=metadata.get('image') or metadata.get('photo'),
        metadata=_metadata_fields(metadata),
        ingredients=ingredients,
        cookware=cookware,
        method_sections=method_sections,
        notes=notes,
        recipe_root=recipe_root,
        site_root=f'../{recipe_root}',
    )


def _recipe_group(item):
    metadata = _metadata_map(item.get('recipe', {}))
    for key in ('course', 'meal', 'category', 'group'):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().title()
    tags = metadata.get('tags', [])
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(',')]
    elif not isinstance(tags, list):
        tags = []
    for tag in tags:
        course = KNOWN_COURSES.get(str(tag).strip().lower())
        if course:
            return course
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


def _servings(metadata):
    servings = (
        metadata.get('servings') or metadata.get('serves') or metadata.get('yield')
    )
    if servings is None:
        return None
    if isinstance(servings, list):
        servings = ', '.join(str(value) for value in servings)
    servings = str(servings).strip()
    return servings if servings.lower().startswith('serve') else f'serves {servings}'


def render_index(recipe_items: list[dict], title: str = 'jonsim') -> str:
    """Render an index page listing all recipes grouped by course."""
    grouped = {}
    for item in recipe_items:
        grouped.setdefault(_recipe_group(item), []).append(item)
    groups = []
    for name in sorted(grouped, key=_group_sort_key):
        items = sorted(
            grouped[name],
            key=lambda item: (
                _metadata_map(item.get('recipe', {})).get('title')
                or item.get('href', '')
            ).lower(),
        )
        recipes = []
        for item in items:
            metadata = _metadata_map(item.get('recipe', {}))
            recipes.append(
                {
                    'title': metadata.get('title') or item.get('href', 'Recipe'),
                    'description': metadata.get('description'),
                    'href': item.get('href', '#'),
                    'time': metadata.get('time')
                    or metadata.get('total_time')
                    or metadata.get('cooking_time'),
                    'servings': _servings(metadata),
                }
            )
        groups.append(
            {
                'name': name,
                'id': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
                'recipes': recipes,
            }
        )
    return TEMPLATES.get_template('index.html').render(title=title, groups=groups)


def render_index_by_ingredient(
    recipe_items: list[dict], title: str = 'Materia — A Kitchen Manual'
) -> str:
    """Render an index page listing all recipes grouped by ingredient."""
    ingredient_map = {}
    for item in recipe_items:
        metadata = _metadata_map(item.get('recipe', {}))
        recipe_title = metadata.get('title') or item.get('href', 'Recipe')
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
        title=title, ingredients=ingredients
    )
