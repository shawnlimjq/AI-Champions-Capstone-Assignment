import unittest

from utils.crawler_utils import extract_ai_friendly_text


class ExtractAiFriendlyTextTests(unittest.TestCase):
    def test_extract_ai_friendly_text_removes_scripts_and_formats(self):
        html = """
        <html>
          <head>
            <title>Example title</title>
            <script>console.log('ignore me')</script>
          </head>
          <body>
            <header>Site header</header>
            <nav>Menu</nav>
            <main>
              <h1>Helpful heading</h1>
              <p>First paragraph with <strong>bold</strong> text.</p>
              <ul>
                <li>One</li>
                <li>Two</li>
              </ul>
            </main>
            <footer>Footer</footer>
          </body>
        </html>
        """

        text = extract_ai_friendly_text(html)

        self.assertIn("Helpful heading", text)
        self.assertIn("First paragraph", text)
        self.assertIn("One", text)
        self.assertIn("Two", text)
        self.assertNotIn("console.log", text)
        self.assertNotIn("Site header", text)
        self.assertNotIn("Menu", text)
        self.assertNotIn("Footer", text)


if __name__ == "__main__":
    unittest.main()
