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
            '<span class="name">flour</span><span class="qty">200 g</span>', rendered
        )
        self.assertIn('<span class="cook">bowl</span>', rendered)
        self.assertIn('<span class="time">2 minutes</span>', rendered)

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


if __name__ == '__main__':
    unittest.main()
