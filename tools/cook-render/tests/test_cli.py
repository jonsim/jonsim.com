import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cook_render import main


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name) / 'recipes'
        self.base_dir.mkdir()
        self.out_dir = Path(self.temp_dir.name) / 'output'

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_renders_recipes_recursively(self):
        # Create a recipe at the root of base_dir and one in a subfolder
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        sub_dir = self.base_dir / 'desserts'
        sub_dir.mkdir()
        (sub_dir / 'cake.cook').write_text('Bake @flour{200%g}.', encoding='utf-8')

        dummy_recipe = {
            'metadata': {'map': {'title': 'Dummy'}},
            'sections': [],
            'ingredients': [],
            'cookware': [],
            'timers': [],
            'inline_quantities': [],
        }

        with patch('cook_render.load_recipe', return_value=dummy_recipe):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 0)

        simple_html = self.out_dir / 'simple.html'
        cake_html = self.out_dir / 'desserts' / 'cake.html'
        index_html = self.out_dir / 'index.html'
        ing_index_html = self.out_dir / 'index_by_ingredient.html'
        recipe_style = self.out_dir / 'recipe_style.css'

        self.assertTrue(simple_html.exists())
        self.assertTrue(cake_html.exists())
        self.assertTrue(index_html.exists())
        self.assertTrue(ing_index_html.exists())
        self.assertTrue(recipe_style.exists())
        self.assertIn('<!doctype html>', simple_html.read_text(encoding='utf-8'))
        self.assertIn(
            'href="index.html">← All recipes</a>',
            simple_html.read_text(encoding='utf-8'),
        )
        self.assertIn('<h1>Dummy.</h1>', cake_html.read_text(encoding='utf-8'))
        self.assertIn(
            'href="../index.html">← All recipes</a>',
            cake_html.read_text(encoding='utf-8'),
        )
        self.assertIn(
            'href="../recipe_style.css"',
            cake_html.read_text(encoding='utf-8'),
        )
        self.assertIn(
            '<a class="project-row" href="simple.html">',
            index_html.read_text(encoding='utf-8'),
        )
        self.assertIn(
            '<a class="project-row" href="desserts/cake.html">',
            index_html.read_text(encoding='utf-8'),
        )
        self.assertIn(
            '<h1>Index by Ingredient</h1>', ing_index_html.read_text(encoding='utf-8')
        )

    def test_nonexistent_base_path(self):
        with self.assertRaises(SystemExit):
            main(['-b', str(self.base_dir / 'does_not_exist')])

    def test_cook_command_not_found(self):
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        with patch('cook_render.load_recipe', side_effect=FileNotFoundError):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 1)

    def test_cook_called_process_error(self):
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        err = subprocess.CalledProcessError(
            returncode=1, cmd=['cook'], stderr='Parse error'
        )
        with patch('cook_render.load_recipe', side_effect=err):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 1)

    def test_cook_json_decode_error(self):
        (self.base_dir / 'simple.cook').write_text('Add @salt.', encoding='utf-8')
        err = json.JSONDecodeError('Expecting value', '', 0)
        with patch('cook_render.load_recipe', side_effect=err):
            ret = main(['-b', str(self.base_dir), '-o', str(self.out_dir)])
            self.assertEqual(ret, 1)

    @unittest.skipUnless(shutil.which('cook'), 'CookCLI is not installed')
    def test_real_cook_execution(self):
        # Run against tests/examples with actual cook CLI if available
        examples_dir = Path(__file__).parent / 'examples'
        ret = main(['-b', str(examples_dir), '-o', str(self.out_dir)])
        self.assertEqual(ret, 0)

        self.assertTrue((self.out_dir / 'index.html').exists())
        self.assertTrue((self.out_dir / 'index_by_ingredient.html').exists())
        self.assertTrue((self.out_dir / 'pancakes.html').exists())
        self.assertTrue((self.out_dir / 'tomato-sauce.html').exists())
        self.assertTrue((self.out_dir / 'minimal.html').exists())

        pancakes_content = (self.out_dir / 'pancakes.html').read_text(encoding='utf-8')
        self.assertIn('<h1>Pancakes.</h1>', pancakes_content)
        self.assertIn('<span>Flour</span>', pancakes_content)

        index_content = (self.out_dir / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<h1>Things I <span>cook</span>.</h1>', index_content)
        self.assertIn('<a class="project-row" href="pancakes.html">', index_content)

        ing_content = (self.out_dir / 'index_by_ingredient.html').read_text(
            encoding='utf-8'
        )
        self.assertIn('<h1>Index by Ingredient</h1>', ing_content)
        self.assertIn('<span class="term">Flour</span>', ing_content)
        self.assertIn('<p><a href="pancakes.html">Pancakes</a></p>', ing_content)
        self.assertIn('<span class="term">Salt</span>', ing_content)
        self.assertIn('<p><a href="minimal.html">Minimal Recipe</a></p>', ing_content)
        self.assertIn(
            '<p><a href="tomato-sauce.html">Tomato Sauce</a></p>', ing_content
        )


if __name__ == '__main__':
    unittest.main()
