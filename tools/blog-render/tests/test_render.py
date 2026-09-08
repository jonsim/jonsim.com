import unittest

import blog_render


class RenderBlogTests(unittest.TestCase):
    def test_renders_blog_posts(self):
        rendered = blog_render.render_blog()

        self.assertTrue(rendered.startswith('<!doctype html>'))


class RenderIndexTests(unittest.TestCase):
    def test_renders_index_page(self):
        rendered = blog_render.render_index()

        self.assertTrue(rendered.startswith('<!doctype html>'))


if __name__ == '__main__':
    unittest.main()
