import unittest

import cook_render


def regular_quantity(value, unit=None):
    return {
        'value': {
            'type': 'number',
            'value': {'type': 'regular', 'value': value},
        },
        'unit': unit,
        'scalable': True,
    }


def pancakes_recipe():
    # This is the shape emitted by `cook recipe -f json`, including the
    # slightly fiddly indices used to refer back to ingredients and cookware.
    return {
        'metadata': {
            'map': {
                'title': "Swedish Chef's Pancakes",
                'description': 'Breakfast for Beaker & Bunsen',
                'servings': 2,
                'tags': ['breakfast', 'quick'],
            }
        },
        'sections': [
            {
                'name': None,
                'content': [
                    {
                        'type': 'step',
                        'value': {
                            'number': 1,
                            'items': [
                                {'type': 'text', 'value': 'Mix '},
                                {'type': 'ingredient', 'index': 0},
                                {'type': 'text', 'value': ' in a '},
                                {'type': 'cookware', 'index': 0},
                                {'type': 'text', 'value': ' for '},
                                {'type': 'timer', 'index': 0},
                                {'type': 'text', 'value': '.'},
                            ],
                        },
                    }
                ],
            }
        ],
        'ingredients': [
            {
                'name': 'flour',
                'alias': None,
                'quantity': regular_quantity(200, 'g'),
                'relation': {
                    'relation': {
                        'type': 'definition',
                        'referenced_from': [],
                        'defined_in_step': True,
                    }
                },
            }
        ],
        'cookware': [
            {
                'name': 'bowl',
                'alias': None,
                'quantity': None,
                'relation': {'type': 'definition', 'referenced_from': []},
            }
        ],
        'timers': [{'name': None, 'quantity': regular_quantity(2, 'minutes')}],
        'inline_quantities': [],
    }


class RenderRecipeTests(unittest.TestCase):
    def test_renders_cookcli_json(self):
        rendered = cook_render.render_recipe(pancakes_recipe())

        self.assertTrue(rendered.startswith('<!DOCTYPE html>'))
        self.assertIn('<title>Swedish Chef&#39;s Pancakes</title>', rendered)
        self.assertIn('family=Goudy+Bookletter+1911', rendered)
        self.assertIn('family=Archivo', rendered)
        self.assertNotIn('From the kitchen', rendered)
        self.assertIn('Breakfast for Beaker &amp; Bunsen', rendered)
        self.assertIn('<dt>tags</dt>', rendered)
        self.assertIn('<dd>breakfast, quick</dd>', rendered)
        self.assertIn('<div class="recipe-top">', rendered)
        self.assertIn(
            '<span class="name">Flour</span><span class="qty">200 g</span>', rendered
        )
        self.assertIn('<span class="cook">bowl</span>', rendered)
        self.assertIn('<span class="time">2 minutes</span>', rendered)

    def test_renders_with_root_path(self):
        rendered = cook_render.render_recipe(pancakes_recipe(), root_path='../')
        self.assertIn(
            '<a class="back" href="../index.html">← Back to contents</a>', rendered
        )
        self.assertIn('<a class="nav-link" href="../index.html">Contents</a>', rendered)
        self.assertIn(
            '<a class="nav-link" href="../index_by_ingredient.html">Ingredient Index</a>',
            rendered,
        )
        self.assertIn(
            '<a class="nav-link" href="../index_by_time.html">Time Index</a>', rendered
        )

    def test_renders_notes_and_named_sections(self):
        recipe = pancakes_recipe()
        recipe['sections'] = [
            {
                'name': 'Batter',
                'content': [
                    {
                        'type': 'step',
                        'value': {
                            'number': 1,
                            'items': [{'type': 'text', 'value': 'Stir gently.'}],
                        },
                    },
                    {
                        'type': 'text',
                        'value': 'Note: Do not overmix.',
                    },
                ],
            }
        ]

        rendered = cook_render.render_recipe(recipe)

        self.assertIn('<h4>Batter</h4>', rendered)
        self.assertIn('<div class="note"><b>Note.</b> Do not overmix.</div>', rendered)

    def test_escapes_recipe_text(self):
        recipe = pancakes_recipe()
        recipe['sections'][0]['content'][0]['value']['items'] = [
            {'type': 'text', 'value': "Keep <script>alert('Animal')</script> away."}
        ]

        rendered = cook_render.render_recipe(recipe)

        self.assertIn(
            'Keep &lt;script&gt;alert(&#39;Animal&#39;)&lt;/script&gt; away.',
            rendered,
        )
        self.assertNotIn('<script>', rendered)


class RenderIndexTests(unittest.TestCase):
    def test_renders_index_page(self):
        recipes = [
            {
                'recipe': pancakes_recipe(),
                'href': 'pancakes.html',
            },
            {
                'recipe': {
                    'metadata': {
                        'map': {
                            'title': 'Burnt Basque Cheesecake',
                            'description': 'Baked hot and fast until the top is nearly black.',
                            'time': '1 hr, plus chilling',
                            'serves': '8-10',
                            'course': 'Dessert',
                        }
                    }
                },
                'href': 'desserts/cheesecake.html',
            },
            {
                'recipe': {
                    'metadata': {
                        'map': {
                            'title': 'Tomato Sauce',
                            'time': '30 min',
                        }
                    }
                },
                'href': 'sauce.html',
            },
        ]

        rendered = cook_render.render_index(recipes)

        self.assertTrue(rendered.startswith('<!DOCTYPE html>'))
        self.assertIn('<title>Materia — A Kitchen Manual</title>', rendered)
        self.assertIn('family=Goudy+Bookletter+1911', rendered)
        self.assertIn('family=Archivo', rendered)
        self.assertIn('<div class="book">', rendered)
        self.assertIn(
            '<div class="mark">jonsim <span>kitchen manual</span></div>', rendered
        )
        self.assertIn(
            '<a class="nav-link is-active" href="index.html">Contents</a>', rendered
        )
        self.assertIn('<h1>Recipes</h1>', rendered)

        # Meal groups
        self.assertIn('<h2 class="section-heading">Breakfast</h2>', rendered)
        self.assertIn('<h2 class="section-heading">Dessert</h2>', rendered)
        self.assertIn('<h2 class="section-heading">Recipes</h2>', rendered)

        # Recipe rows
        self.assertIn('<a class="recipe-row" href="pancakes.html">', rendered)
        self.assertIn(
            '<span class="row-title">Swedish Chef&#39;s Pancakes</span>', rendered
        )
        self.assertIn(
            '<span class="row-desc">Breakfast for Beaker &amp; Bunsen</span>', rendered
        )
        self.assertIn('<span class="row-meta">serves 2</span>', rendered)

        self.assertIn(
            '<a class="recipe-row" href="desserts/cheesecake.html">', rendered
        )
        self.assertIn(
            '<span class="row-title">Burnt Basque Cheesecake</span>', rendered
        )
        self.assertIn(
            '<span class="row-meta">1 hr, plus chilling — serves 8-10</span>', rendered
        )

        self.assertIn('<a class="recipe-row" href="sauce.html">', rendered)
        self.assertIn('<span class="row-title">Tomato Sauce</span>', rendered)
        self.assertIn('<span class="row-meta">30 min</span>', rendered)

    def test_renders_empty_index_page(self):
        rendered = cook_render.render_index([])
        self.assertTrue(rendered.startswith('<!DOCTYPE html>'))
        self.assertIn('<h1>Recipes</h1>', rendered)
        self.assertNotIn('<div class="meal-group">', rendered)


class RenderIndexByIngredientTests(unittest.TestCase):
    def test_renders_ingredient_index_page(self):
        recipes = [
            {
                'recipe': pancakes_recipe(),
                'href': 'pancakes.html',
            },
            {
                'recipe': {
                    'metadata': {
                        'map': {
                            'title': 'Burnt Basque Cheesecake',
                        }
                    },
                    'ingredients': [
                        {'name': 'cream cheese'},
                        {'name': 'eggs'},
                        {'name': 'caster sugar'},
                    ],
                },
                'href': 'cheesecake.html',
            },
        ]

        rendered = cook_render.render_index_by_ingredient(recipes)

        self.assertTrue(rendered.startswith('<!DOCTYPE html>'))
        self.assertIn('<title>Materia — A Kitchen Manual</title>', rendered)
        self.assertIn('family=Goudy+Bookletter+1911', rendered)
        self.assertIn('family=Archivo', rendered)
        self.assertIn('<div class="book">', rendered)
        self.assertIn(
            '<a class="nav-link is-active" href="index_by_ingredient.html">Ingredient Index</a>',
            rendered,
        )
        self.assertIn('<h1>Index by Ingredient</h1>', rendered)
        self.assertIn('<ul class="ingredient-index">', rendered)

        # Terms formatted with capitalize() and sorted
        self.assertIn('<span class="term">Caster sugar</span>', rendered)
        self.assertIn('<span class="term">Cream cheese</span>', rendered)
        self.assertIn('<span class="term">Eggs</span>', rendered)
        self.assertIn('<span class="term">Flour</span>', rendered)

        # Links to recipes
        self.assertIn(
            '<p><a href="cheesecake.html">Burnt Basque Cheesecake</a></p>', rendered
        )
        self.assertIn(
            '<p><a href="pancakes.html">Swedish Chef&#39;s Pancakes</a></p>', rendered
        )

    def test_renders_empty_ingredient_index_page(self):
        rendered = cook_render.render_index_by_ingredient([])
        self.assertTrue(rendered.startswith('<!DOCTYPE html>'))
        self.assertIn('<h1>Index by Ingredient</h1>', rendered)
        self.assertIn('<ul class="ingredient-index">\n        </ul>', rendered)


if __name__ == '__main__':
    unittest.main()
