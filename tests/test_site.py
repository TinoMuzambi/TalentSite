from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.external_runtime_references = []
        self.h1_count = 0
        self.has_lang = False
        self.has_viewport = False
        self.inline_styles = []
        self.inline_scripts = 0
        self._script_has_src = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "html":
            self.has_lang = bool(attributes.get("lang"))
        if tag == "meta" and attributes.get("name") == "viewport":
            self.has_viewport = True
        if tag == "h1":
            self.h1_count += 1
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if "style" in attributes:
            self.inline_styles.append(tag)

        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"img", "script"} else None
        if attribute and attributes.get(attribute):
            reference = attributes[attribute]
            if tag in {"img", "script", "link"} and reference.startswith(("http://", "https://")):
                self.external_runtime_references.append(reference)
            elif reference.startswith("/") and not reference.startswith("//"):
                self.references.append(reference)

        if tag == "script":
            self._script_has_src = "src" in attributes

    def handle_endtag(self, tag):
        if tag == "script" and not self._script_has_src:
            self.inline_scripts += 1


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.parser = SiteParser()
        cls.parser.feed(cls.html)

    def test_document_has_accessibility_basics(self):
        self.assertTrue(self.parser.has_lang)
        self.assertTrue(self.parser.has_viewport)
        self.assertEqual(self.parser.h1_count, 1)
        self.assertIn('class="skip-link"', self.html)

    def test_ids_are_unique(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))

    def test_local_assets_exist(self):
        missing = []
        for reference in self.parser.references:
            path = urlparse(reference).path.lstrip("/")
            if path and not (ROOT / path).exists():
                missing.append(reference)
        self.assertEqual(missing, [])

    def test_runtime_has_no_third_party_dependencies(self):
        self.assertEqual(self.parser.external_runtime_references, [])
        self.assertEqual(self.parser.inline_scripts, 0)
        self.assertEqual(self.parser.inline_styles, [])


if __name__ == "__main__":
    unittest.main()
