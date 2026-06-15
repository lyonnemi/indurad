import unittest
from docutils.utils import new_document
from indurad_ci_sphinx_extensions.util import (
    get_document_source,
)


class TestUtilFunctions(unittest.TestCase):
    def test_get_document_source(self) -> None:
        expected_source = "/path_to_workspace/module/path_to_file/README.rst"
        document = new_document(expected_source)
        output = str(get_document_source(document))
        self.assertEqual(expected_source, output)
