"""Turn CookCLI's JSON recipe output into a standalone HTML page."""

import html
import json
from importlib import resources


def _embedded_style() -> str:
    """Embed the stylesheet into the page."""
    style = (
        resources.files('cook_render').joinpath('style.css').read_text(encoding='utf-8')
    )
    return f'\n<style>\n{style}\n</style>\n'


def _escape(value):
    """Escape a value before putting it into the page."""
    # html.escape uses &#x27; for apostrophes. &#39; is equivalent, but keeping
    # the Rust renderer's spelling makes generated pages easier to compare.
    return html.escape(str(value), quote=True).replace('&#x27;', '&#39;')


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
    """Get the component relation nested inside an ingredient relation."""
    relation = ingredient.get('relation', {})
    return relation.get('relation', relation)


def _is_definition(component, *, ingredient=False):
    """Say whether a component belongs in the summary list."""
    relation = (
        _ingredient_relation(component) if ingredient else component.get('relation', {})
    )
    return relation.get('type', 'definition') == 'definition'


def _grouped_quantity(ingredient, ingredients):
    """Combine an ingredient's own quantity with quantities on references."""
    relation = _ingredient_relation(ingredient)
    indices = relation.get('referenced_from', [])
    quantities = [ingredient.get('quantity')]
    quantities.extend(ingredients[index].get('quantity') for index in indices)
    quantities = [quantity for quantity in quantities if quantity]
    if not quantities:
        return ''

    # Cooklang can convert compatible units too. This prototype only adds
    # quantities already using the same unit; anything else remains readable.
    units = {quantity.get('unit') for quantity in quantities}
    numbers = [_quantity_number(quantity) for quantity in quantities]
    if len(units) == 1 and all(number is not None for number in numbers):
        total = sum(numbers)
        quantity = dict(quantities[0])
        quantity['value'] = {
            'type': 'number',
            'value': {'type': 'regular', 'value': total},
        }
        return _format_quantity(quantity)

    return ', '.join(_format_quantity(quantity) for quantity in quantities)


def _metadata_map(recipe):
    """Return metadata from the current CookCLI JSON shape."""
    metadata = recipe.get('metadata', recipe.get('raw_metadata', {}))
    return metadata.get('map', metadata)


def render_metadata(recipe):
    """Render recipe metadata other than the title and description."""
    fields = []
    for key, value in sorted(_metadata_map(recipe).items()):
        if key in {'title', 'description'}:
            continue
        if isinstance(value, list):
            display_value = ', '.join(str(item) for item in value)
        elif isinstance(value, str):
            display_value = value
        else:
            display_value = json.dumps(value, separators=(',', ':'))
        fields.append(
            '              <div>\n'
            f'                <dt>{_escape(key)}</dt>\n'
            f'                <dd>{_escape(display_value)}</dd>\n'
            '              </div>'
        )

    if not fields:
        return ''
    return (
        '            <dl class="metadata">\n'
        + '\n'.join(fields)
        + '\n            </dl>\n'
    )


def render_requirements(recipe):
    """Render the ingredient and cookware summary lists."""
    sections = []
    ingredients = recipe.get('ingredients', [])
    ingredient_rows = []
    for ingredient in ingredients:
        if not _is_definition(ingredient, ingredient=True):
            continue
        name = ingredient.get('alias') or ingredient.get('name', '')
        name = name.title()
        quantity = _grouped_quantity(ingredient, ingredients)
        quantity_html = (
            f'<span class="qty">{_escape(quantity)}</span>' if quantity else ''
        )
        ingredient_rows.append(
            f'                <li><span class="name">{_escape(name)}</span>{quantity_html}</li>'
        )
    if ingredient_rows:
        sections.append(
            '            <div class="ingredients">\n'
            '              <h3 class="section-heading">Ingredients</h3>\n'
            '              <ul class="items">\n'
            + '\n'.join(ingredient_rows)
            + '\n              </ul>\n'
            '            </div>\n'
        )

    cookware_rows = []
    for cookware in recipe.get('cookware', []):
        if not _is_definition(cookware):
            continue
        name = cookware.get('alias') or cookware.get('name', '')
        name = name.title()
        quantity = _format_quantity(cookware.get('quantity'))
        quantity_html = (
            f'<span class="qty">{_escape(quantity)}</span>' if quantity else ''
        )
        cookware_rows.append(
            f'                <li><span class="name">{_escape(name)}</span>{quantity_html}</li>'
        )
    if cookware_rows:
        sections.append(
            '            <div class="cookware">\n'
            '              <h3 class="section-heading">Cookware</h3>\n'
            '              <ul class="items">\n'
            + '\n'.join(cookware_rows)
            + '\n              </ul>\n'
            '            </div>\n'
        )

    if not sections:
        return ''
    return (
        '          <div class="recipe-top">\n'
        + ''.join(sections)
        + '          </div>\n'
    )


def render_step(recipe, item):
    """Render one item from Cooklang's index-based step representation."""
    kind = item.get('type')
    if kind == 'text':
        return _escape(item.get('value', ''))
    if kind == 'ingredient':
        ingredient = recipe['ingredients'][item['index']]
        name = ingredient.get('alias') or ingredient.get('name', '')
        quantity = _format_quantity(ingredient.get('quantity'))
        quantity_html = (
            f' <span class="qty">({_escape(quantity)})</span>' if quantity else ''
        )
        return f'<span class="ing">{_escape(name)}{quantity_html}</span>'
    if kind == 'cookware':
        cookware = recipe['cookware'][item['index']]
        name = cookware.get('alias') or cookware.get('name', '')
        quantity = _format_quantity(cookware.get('quantity'))
        quantity_html = (
            f' <span class="qty">({_escape(quantity)})</span>' if quantity else ''
        )
        return f'<span class="cook">{_escape(name)}{quantity_html}</span>'
    if kind == 'timer':
        timer = recipe['timers'][item['index']]
        parts = [timer.get('name'), _format_quantity(timer.get('quantity'))]
        return f'<span class="time">{_escape(" ".join(part for part in parts if part))}</span>'
    if kind == 'inlineQuantity':
        quantity = recipe['inline_quantities'][item['index']]
        return f'<span class="qty">{_escape(_format_quantity(quantity))}</span>'
    return ''


def render_method(recipe):
    """Render recipe sections, text blocks and numbered steps."""
    parts = [
        '          <div class="method-section">\n'
        '            <h3 class="section-heading">Method</h3>\n'
    ]
    for section in recipe.get('sections', []):
        if section.get('name'):
            parts.append(f'            <h4>{_escape(section["name"])}</h4>\n')
        in_list = False
        for content in section.get('content', []):
            if content.get('type') == 'step':
                if not in_list:
                    parts.append('            <ol>\n')
                    in_list = True
                step = content.get('value', {})
                body = ''.join(
                    render_step(recipe, item) for item in step.get('items', [])
                )
                parts.append(
                    f'              <li>\n                <p>{body}</p>\n              </li>\n'
                )
            elif content.get('type') == 'text':
                if in_list:
                    parts.append('            </ol>\n')
                    in_list = False
                val = content.get('value', '').strip()
                lower_val = val.lower()
                if lower_val.startswith(('note:', 'note.')):
                    note_text = val[5:].strip()
                    parts.append(
                        f'            <div class="note"><b>Note.</b> {_escape(note_text)}</div>\n'
                    )
                elif lower_val.startswith('note'):
                    note_text = val[4:].lstrip(' -:.\t').strip()
                    parts.append(
                        f'            <div class="note"><b>Note.</b> {_escape(note_text)}</div>\n'
                    )
                else:
                    parts.append(f'            <p>{_escape(val)}</p>\n')
        if in_list:
            parts.append('            </ol>\n')
    parts.append('          </div>\n')
    return ''.join(parts)


def render_recipe(recipe, root_path: str | int = ''):
    """Render one CookCLI JSON recipe as a complete HTML document."""
    if isinstance(root_path, int):
        root_prefix = '../' * root_path
    else:
        root_prefix = str(root_path)
        if root_prefix and not root_prefix.endswith('/'):
            root_prefix += '/'

    metadata = _metadata_map(recipe)
    title = metadata.get('title') or 'Recipe'
    description = metadata.get('description')
    description_html = (
        f'            <p class="dek">\n              {_escape(description)}\n            </p>\n'
        if description
        else ''
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n\n<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <title>{_escape(title)}</title>\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link\n'
        '    href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600&family=Goudy+Bookletter+1911&display=swap"\n'
        '    rel="stylesheet">\n'
        f'{_embedded_style()}'
        '</head>\n\n'
        '<body>\n'
        '  <div class="book">\n'
        '    <header class="topbar">\n'
        f'      <a class="back" href="{root_prefix}index.html">← Back to contents</a>\n'
        '      <nav>\n'
        f'        <a class="nav-link" href="{root_prefix}index.html">Contents</a>\n'
        f'        <a class="nav-link" href="{root_prefix}index_by_ingredient.html">Ingredient Index</a>\n'
        f'        <a class="nav-link" href="{root_prefix}index_by_time.html">Time Index</a>\n'
        '      </nav>\n'
        '    </header>\n'
        '    <main>\n'
        '      <section>\n'
        '        <article>\n'
        '          <div class="recipe-head">\n'
        f'            <h2>{_escape(title)}</h2>\n'
        f'{description_html}'
        f'{render_metadata(recipe)}'
        '          </div>\n'
        f'{render_requirements(recipe)}'
        f'{render_method(recipe)}'
        '        </article>\n'
        '      </section>\n'
        '    </main>\n'
        '  </div>\n'
        '</body>\n\n'
        '</html>\n'
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


def _recipe_group(item: dict) -> str:
    """Determine the meal group / course for a recipe."""
    recipe = item.get('recipe', {})
    metadata = _metadata_map(recipe)

    # 1. Explicit course / meal / category in metadata
    for key in ('course', 'meal', 'category', 'group'):
        val = metadata.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip().title()

    # 2. Check tags
    tags = metadata.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',')]
    elif not isinstance(tags, list):
        tags = []

    known_courses = {
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

    for tag in tags:
        tag_lower = str(tag).strip().lower()
        if tag_lower in known_courses:
            return known_courses[tag_lower]

    # 3. Relative parent directory name
    rel_path = item.get('relative_path')
    if rel_path and rel_path.parent and str(rel_path.parent) != '.':
        parent_name = rel_path.parent.parts[0]
        parent_lower = parent_name.lower()
        if parent_lower in known_courses:
            return known_courses[parent_lower]
        return parent_name.replace('-', ' ').replace('_', ' ').title()

    return 'Recipes'


def _format_row_meta(metadata: dict) -> str:
    """Format time and servings metadata for the recipe row."""
    time = (
        metadata.get('time')
        or metadata.get('total_time')
        or metadata.get('cooking_time')
    )
    servings = (
        metadata.get('servings') or metadata.get('serves') or metadata.get('yield')
    )
    if isinstance(servings, list):
        servings = ', '.join(str(s) for s in servings)

    time_str = str(time).strip() if time else ''
    servings_str = str(servings).strip() if servings is not None else ''
    if servings_str and not servings_str.lower().startswith('serve'):
        servings_str = f'serves {servings_str}'

    if time_str and servings_str:
        return f'{time_str} — {servings_str}'
    if time_str:
        return time_str
    if servings_str:
        return servings_str
    return ''


def render_index(
    recipe_items: list[dict], title: str = 'Materia — A Kitchen Manual'
) -> str:
    """Render an index page listing all recipes grouped by meal."""
    grouped: dict[str, list[dict]] = {}
    for item in recipe_items:
        group = _recipe_group(item)
        grouped.setdefault(group, []).append(item)

    def group_sort_key(name: str):
        if name in COURSE_ORDER:
            return (0, COURSE_ORDER.index(name))
        if name in ('Recipes', 'Other'):
            return (2, name)
        return (1, name)

    group_sections = []
    for group_name in sorted(grouped.keys(), key=group_sort_key):
        items = grouped[group_name]
        items = sorted(
            items,
            key=lambda it: (
                _metadata_map(it.get('recipe', {})).get('title') or it.get('href', '')
            ).lower(),
        )

        rows = []
        for it in items:
            recipe = it.get('recipe', {})
            metadata = _metadata_map(recipe)
            recipe_title = metadata.get('title') or it.get('href', 'Recipe')
            description = metadata.get('description')
            href = it.get('href', '#')
            meta_str = _format_row_meta(metadata)

            desc_html = (
                f'<span class="row-desc">{_escape(description)}</span>'
                if description
                else ''
            )
            meta_html = (
                f'<span class="row-meta">{_escape(meta_str)}</span>' if meta_str else ''
            )

            rows.append(
                '              <li>'
                f'<a class="recipe-row" href="{_escape(href)}">'
                '<span class="row-main">'
                f'<span class="row-title">{_escape(recipe_title)}</span>'
                f'{desc_html}'
                '</span>'
                f'{meta_html}'
                '</a>'
                '</li>'
            )

        group_sections.append(
            '          <div class="meal-group">\n'
            f'            <h2 class="section-heading">{_escape(group_name)}</h2>\n'
            '            <ol class="recipe-list">\n'
            + '\n'.join(rows)
            + '\n            </ol>\n'
            '          </div>\n'
        )

    contents_body = ''.join(group_sections)

    return (
        '<!DOCTYPE html>\n<html lang="en">\n\n<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <title>{_escape(title)}</title>\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link\n'
        '    href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600&family=Goudy+Bookletter+1911&display=swap"\n'
        '    rel="stylesheet">\n'
        f'{_embedded_style()}'
        '</head>\n\n'
        '<body>\n'
        '  <div class="book">\n'
        '    <header class="topbar">\n'
        '      <div class="mark">jonsim <span>kitchen manual</span></div>\n'
        '      <nav>\n'
        '        <a class="nav-link is-active" href="index.html">Contents</a>\n'
        '        <a class="nav-link" href="index_by_ingredient.html">Ingredient Index</a>\n'
        '        <a class="nav-link" href="index_by_time.html">Time Index</a>\n'
        '      </nav>\n'
        '    </header>\n'
        '    <main>\n'
        '      <section>\n'
        '        <div class="page-intro">\n'
        '          <h1>Recipes</h1>\n'
        '        </div>\n'
        '        <div class="contents">\n'
        f'{contents_body}'
        '        </div>\n'
        '      </section>\n'
        '    </main>\n'
        '  </div>\n'
        '</body>\n\n'
        '</html>\n'
    )


def render_index_by_ingredient(
    recipe_items: list[dict], title: str = 'Materia — A Kitchen Manual'
) -> str:
    """Render an index page listing all recipes grouped by ingredient."""
    ingredient_map: dict[str, dict] = {}

    for item in recipe_items:
        recipe = item.get('recipe', {})
        metadata = _metadata_map(recipe)
        recipe_title = metadata.get('title') or item.get('href', 'Recipe')
        href = item.get('href', '#')

        seen_for_recipe = set()
        for ing in recipe.get('ingredients', []):
            raw_name = (ing.get('name') or ing.get('alias') or '').strip()
            if not raw_name:
                continue
            normalized = raw_name.lower()
            if normalized in seen_for_recipe:
                continue
            seen_for_recipe.add(normalized)

            if normalized not in ingredient_map:
                ingredient_map[normalized] = {
                    'term': raw_name.capitalize(),
                    'recipes': [],
                }
            ingredient_map[normalized]['recipes'].append(
                {'title': recipe_title, 'href': href}
            )

    rows = []
    for norm_key in sorted(
        ingredient_map.keys(), key=lambda k: ingredient_map[k]['term'].lower()
    ):
        data = ingredient_map[norm_key]
        term = data['term']
        sorted_recipes = sorted(data['recipes'], key=lambda r: r['title'].lower())

        refs_html = '\n'.join(
            f'              <p><a href="{_escape(r["href"])}">{_escape(r["title"])}</a></p>'
            for r in sorted_recipes
        )

        rows.append(
            '          <li>\n'
            f'            <span class="term">{_escape(term)}</span>\n'
            '            <span class="refs">\n'
            f'{refs_html}\n'
            '            </span>\n'
            '          </li>'
        )

    items_body = '\n'.join(rows)
    if items_body:
        items_body += '\n'

    return (
        '<!DOCTYPE html>\n<html lang="en">\n\n<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <title>{_escape(title)}</title>\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link\n'
        '    href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600&family=Goudy+Bookletter+1911&display=swap"\n'
        '    rel="stylesheet">\n'
        f'{_embedded_style()}'
        '</head>\n\n'
        '<body>\n'
        '  <div class="book">\n'
        '    <header class="topbar">\n'
        '      <div class="mark">jonsim <span>kitchen manual</span></div>\n'
        '      <nav>\n'
        '        <a class="nav-link" href="index.html">Contents</a>\n'
        '        <a class="nav-link is-active" href="index_by_ingredient.html">Ingredient Index</a>\n'
        '        <a class="nav-link" href="index_by_time.html">Time Index</a>\n'
        '      </nav>\n'
        '    </header>\n'
        '    <main>\n'
        '      <section id="ingredient-index">\n'
        '        <div class="page-intro">\n'
        '          <h1>Index by Ingredient</h1>\n'
        '        </div>\n'
        '        <ul class="ingredient-index">\n'
        f'{items_body}'
        '        </ul>\n'
        '      </section>\n'
        '    </main>\n'
        '  </div>\n'
        '</body>\n\n'
        '</html>\n'
    )
