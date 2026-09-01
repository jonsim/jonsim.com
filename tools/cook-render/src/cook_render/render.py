"""Turn CookCLI's JSON recipe output into a standalone HTML page."""

import html
import json

STYLES = """\
  <style>
    :root {
      --paper: #f7f6f2;
      --ink: #252422;
      --muted-ink: #69655f;
      --rule: #c8c4bc;
      --accent: #7f2f2a;
      font-family: "Goudy Bookletter 1911", Georgia, serif;
      color: var(--ink);
      background: #d5d3ce;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: clamp(1rem, 4vw, 4rem);
      background:
        radial-gradient(circle at 15% 8%, rgb(255 255 255 / 35%), transparent 26rem),
        linear-gradient(135deg, #dedcd7, #cbc8c1);
    }
    main {
      position: relative;
      max-width: 64rem;
      min-height: calc(100vh - 8rem);
      margin: 0 auto;
      padding: clamp(2.5rem, 7vw, 6.5rem);
      overflow: hidden;
      border: 1px solid #b8b4ac;
      outline: 1px solid rgb(255 255 255 / 55%);
      outline-offset: -9px;
      background: var(--paper);
      box-shadow: 0 2rem 5rem rgb(48 46 41 / 25%), 0 .3rem 1rem rgb(48 46 41 / 12%);
    }
    .recipe-header {
      position: relative;
      margin-bottom: 4.5rem;
      text-align: center;
    }
    .recipe-header::after {
      display: block;
      width: 8rem;
      margin: 2.25rem auto 0;
      border-top: 1px solid var(--rule);
      color: var(--accent);
      line-height: 0;
      content: "✦";
    }
    h1 {
      max-width: 48rem;
      margin: 0 auto;
      font-size: clamp(3.2rem, 9vw, 6.75rem);
      font-weight: 400;
      font-variant-caps: small-caps;
      letter-spacing: .025em;
      line-height: .92;
      text-wrap: balance;
    }
    .description {
      max-width: 34rem;
      margin: 1.5rem auto 0;
      color: var(--muted-ink);
      font-size: 1.35rem;
      font-style: italic;
      line-height: 1.45;
    }
    .metadata {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 1rem 3.5rem;
      margin: 2.25rem 0 0;
    }
    .metadata div { display: grid; gap: .2rem; }
    .metadata dt {
      color: var(--accent);
      font-family: ui-sans-serif, system-ui, sans-serif;
      font-size: .62rem;
      font-weight: 700;
      letter-spacing: .2em;
      text-transform: uppercase;
    }
    .metadata dd { margin: 0; font-size: 1.08rem; }
    .recipe-notes {
      display: grid;
      grid-template-columns: minmax(0, 3fr) minmax(12rem, 2fr);
      gap: clamp(2.5rem, 7vw, 5.5rem);
      margin-bottom: 4.5rem;
    }
    section { min-width: 0; }
    h2 {
      display: flex;
      align-items: baseline;
      gap: .8rem;
      margin: 0 0 1.25rem;
      color: var(--accent);
      font-size: 2.15rem;
      font-weight: 400;
      line-height: 1;
    }
    h2::after { flex: 1; border-top: 1px solid var(--rule); content: ""; }
    h3 {
      margin: 2.5rem 0 1rem;
      color: var(--muted-ink);
      font-family: ui-sans-serif, system-ui, sans-serif;
      font-size: .72rem;
      letter-spacing: .2em;
      text-transform: uppercase;
    }
    .components { margin: 0; padding: 0; list-style: none; }
    .components li {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 1rem;
      padding: .48rem 0;
      border-bottom: 1px dotted var(--rule);
      font-size: 1.08rem;
    }
    .quantity {
      color: var(--muted-ink);
      white-space: nowrap;
      font-variant-numeric: tabular-nums;
    }
    .step {
      display: grid;
      grid-template-columns: 2.75rem 1fr;
      gap: 1.25rem;
      margin: 1.75rem 0;
    }
    .step p { margin: 0; font-size: 1.2rem; line-height: 1.65; }
    .step-number {
      padding-top: .08rem;
      border-right: 1px solid var(--rule);
      color: var(--accent);
      font-size: 2rem;
      line-height: 1;
    }
    .ingredient { color: var(--accent); }
    .cookware { color: var(--muted-ink); font-style: italic; }
    .timer {
      padding: .05rem .28rem;
      border-bottom: 1px solid var(--accent);
      color: var(--accent);
      white-space: nowrap;
    }
    @media (max-width: 42rem) {
      body { padding: 0; }
      main { min-height: 100vh; padding: 4rem 1.6rem; border: 0; outline: 0; }
      .recipe-header { margin-bottom: 3.5rem; }
      .recipe-notes { grid-template-columns: 1fr; gap: 3rem; margin-bottom: 3.5rem; }
      .metadata { gap: 1rem 2rem; }
    }
    @media print {
      :root { background: white; }
      body { padding: 0; background: white; }
      main { max-width: none; min-height: 0; padding: 1cm; border: 0; outline: 0; box-shadow: none; }
    }
  </style>
"""


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
            f'    <div><dt>{_escape(key)}</dt><dd>{_escape(display_value)}</dd></div>'
        )

    if not fields:
        return ''
    return '  <dl class="metadata">\n' + '\n'.join(fields) + '\n  </dl>\n'


def render_requirements(recipe):
    """Render the ingredient and cookware summary lists."""
    sections = []
    ingredients = recipe.get('ingredients', [])
    ingredient_rows = []
    for ingredient in ingredients:
        if not _is_definition(ingredient, ingredient=True):
            continue
        name = ingredient.get('alias') or ingredient.get('name', '')
        quantity = _grouped_quantity(ingredient, ingredients)
        quantity_html = (
            f'<span class="quantity">{_escape(quantity)}</span>' if quantity else ''
        )
        ingredient_rows.append(
            f'    <li><span>{_escape(name)}</span>{quantity_html}</li>'
        )
    if ingredient_rows:
        sections.append(
            '<section>\n  <h2>Ingredients</h2>\n  <ul class="components">\n'
            + '\n'.join(ingredient_rows)
            + '\n  </ul>\n</section>\n'
        )

    cookware_rows = []
    for cookware in recipe.get('cookware', []):
        if not _is_definition(cookware):
            continue
        name = cookware.get('alias') or cookware.get('name', '')
        quantity = _format_quantity(cookware.get('quantity'))
        quantity_html = (
            f'<span class="quantity">{_escape(quantity)}</span>' if quantity else ''
        )
        cookware_rows.append(
            f'    <li><span>{_escape(name)}</span>{quantity_html}</li>'
        )
    if cookware_rows:
        sections.append(
            '<section>\n  <h2>Cookware</h2>\n  <ul class="components">\n'
            + '\n'.join(cookware_rows)
            + '\n  </ul>\n</section>\n'
        )

    if not sections:
        return ''
    return '<div class="recipe-notes">\n' + ''.join(sections) + '</div>\n'


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
            f' <span class="quantity">({_escape(quantity)})</span>' if quantity else ''
        )
        return f'<span class="ingredient">{_escape(name)}{quantity_html}</span>'
    if kind == 'cookware':
        cookware = recipe['cookware'][item['index']]
        name = cookware.get('alias') or cookware.get('name', '')
        quantity = _format_quantity(cookware.get('quantity'))
        quantity_html = (
            f' <span class="quantity">({_escape(quantity)})</span>' if quantity else ''
        )
        return f'<span class="cookware">{_escape(name)}{quantity_html}</span>'
    if kind == 'timer':
        timer = recipe['timers'][item['index']]
        parts = [timer.get('name'), _format_quantity(timer.get('quantity'))]
        return f'<span class="timer">{_escape(" ".join(part for part in parts if part))}</span>'
    if kind == 'inlineQuantity':
        quantity = recipe['inline_quantities'][item['index']]
        return f'<span class="quantity">{_escape(_format_quantity(quantity))}</span>'
    return ''


def render_method(recipe):
    """Render recipe sections, text blocks and numbered steps."""
    parts = ['<section>\n  <h2>Method</h2>\n']
    for section in recipe.get('sections', []):
        if section.get('name'):
            parts.append(f'  <h3>{_escape(section["name"])}</h3>\n')
        for content in section.get('content', []):
            if content.get('type') == 'text':
                parts.append(f'  <p>{_escape(content.get("value", ""))}</p>\n')
                continue
            if content.get('type') != 'step':
                continue

            step = content.get('value', {})
            body = ''.join(render_step(recipe, item) for item in step.get('items', []))
            parts.append(
                f'  <div class="step"><span class="step-number">{step.get("number", "")}</span>'
                f'<p>{body}</p></div>\n'
            )
    parts.append('</section>\n')
    return ''.join(parts)


def render_recipe(recipe):
    """Render one CookCLI JSON recipe as a complete HTML document."""
    metadata = _metadata_map(recipe)
    title = metadata.get('title') or 'Recipe'
    description = metadata.get('description')
    description_html = (
        f'  <p class="description">{_escape(description)}</p>\n' if description else ''
    )

    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'  <title>{_escape(title)}</title>\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link href="https://fonts.googleapis.com/css2?family=Goudy+Bookletter+1911&display=swap" rel="stylesheet">\n'
        f'{STYLES}</head>\n<body>\n<main>\n<header class="recipe-header">\n'
        f'  <h1>{_escape(title)}</h1>\n'
        f'{description_html}{render_metadata(recipe)}</header>\n'
        f'{render_requirements(recipe)}{render_method(recipe)}'
        '</main>\n</body>\n</html>\n'
    )
