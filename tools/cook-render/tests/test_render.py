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

        self.assertTrue(rendered.startswith('<!doctype html>'))
        self.assertIn('<title>jonsim | Swedish Chef&#39;s Pancakes</title>', rendered)
        self.assertIn('family=DM+Sans', rendered)
        self.assertIn('family=Lekton', rendered)
        self.assertNotIn('From the kitchen', rendered)
        self.assertIn('Breakfast for Beaker &amp; Bunsen', rendered)
        self.assertIn('<dt>Tags</dt>', rendered)
        self.assertIn(
            '<dd class="tags"><span>breakfast</span><span>quick</span></dd>',
            rendered,
        )
        self.assertIn('<section id="recipe-body" class="recipe-body">', rendered)
        self.assertIn(
            '<li><span class="qty">200 g</span><span>Flour</span></li>', rendered
        )
        self.assertIn('<span class="cook">bowl</span>', rendered)
        self.assertIn('<span class="time">2 minutes</span>', rendered)
        self.assertNotIn('Mushroom &amp; pumpkin wellington', rendered)
        self.assertNotIn('{{', rendered)

    def test_renders_recipe_image_from_metadata(self):
        recipe = pancakes_recipe()
        recipe['metadata']['map']['image'] = 'pancakes.jpg'

        rendered = cook_render.render_recipe(recipe)

        self.assertIn(
            '<img src="pancakes.jpg" alt="Swedish Chef&#39;s Pancakes">', rendered
        )
        self.assertNotIn('<dt>Image</dt>', rendered)

    def test_renders_with_root_path(self):
        rendered = cook_render.render_recipe(pancakes_recipe(), root_path='../')
        self.assertIn(
            '<a class="back-link" href="../index.html">← All recipes</a>', rendered
        )
        self.assertIn(
            '<link rel="stylesheet" type="text/css" href="../recipe_style.css">',
            rendered,
        )
        self.assertIn('<a href="../index.html" class="is-active">Recipes</a>', rendered)

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

        self.assertIn('<h3>Batter</h3>', rendered)
        self.assertIn('<section id="notes">', rendered)
        self.assertIn('<p>Do not overmix.</p>', rendered)

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

        self.assertTrue(rendered.startswith('<!doctype html>'))
        self.assertIn('<title>jonsim</title>', rendered)
        self.assertIn('family=DM+Sans', rendered)
        self.assertIn('family=Lekton', rendered)
        self.assertIn('<a class="brand" href="../index.html">jonsim</a>', rendered)
        self.assertIn('<h1>Things I <span>cook</span>.</h1>', rendered)

        # Meal groups
        self.assertIn('<h2>Breakfast</h2>', rendered)
        self.assertIn('<h2>Dessert</h2>', rendered)
        self.assertIn('<h2>Recipes</h2>', rendered)

        # Recipe rows
        self.assertIn('<a class="project-row" href="pancakes.html">', rendered)
        self.assertIn(
            '<h3 class="row-title">Swedish Chef&#39;s Pancakes</h3>', rendered
        )
        self.assertIn(
            '<p class="row-desc">Breakfast for Beaker &amp; Bunsen</p>', rendered
        )
        self.assertIn('<span class="row-serves">serves 2</span>', rendered)

        self.assertIn(
            '<a class="project-row" href="desserts/cheesecake.html">', rendered
        )
        self.assertIn('<h3 class="row-title">Burnt Basque Cheesecake</h3>', rendered)
        self.assertIn('<span class="row-time">1 hr, plus chilling</span>', rendered)
        self.assertIn('<span class="row-serves">serves 8-10</span>', rendered)

        self.assertIn('<a class="project-row" href="sauce.html">', rendered)
        self.assertIn('<h3 class="row-title">Tomato Sauce</h3>', rendered)
        self.assertIn('<span class="row-time">30 min</span>', rendered)
        self.assertNotIn("Jon's Christmas Muesli", rendered)
        self.assertNotIn('{{', rendered)

    def test_renders_empty_index_page(self):
        rendered = cook_render.render_index([])
        self.assertTrue(rendered.startswith('<!doctype html>'))
        self.assertIn('<h1>Things I <span>cook</span>.</h1>', rendered)
        self.assertNotIn('<ol class="project-list">', rendered)


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
