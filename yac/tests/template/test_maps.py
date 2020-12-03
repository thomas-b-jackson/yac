import unittest, os, random
from yac.lib.template import apply_stemplate, apply_ftemplate, apply_templates_in_dir
from yac.lib.file import get_file_contents
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    # test rendering templates in a string
    def test_stemplate(self):

        test_file = 'yac/tests/template/vectors/sample_map_file.txt'

        test_variables = {
            "user-name": {"value": "henry-grantham"},
            "neighborhood-map": {
              "lookup":  "user-name",
              "value": {
                "tom-jackson":    "phinney",
                "henry-grantham": "capital-hill"
              }
            }
        }

        # read file into string
        file_contents = get_file_contents(test_file)

        # run test
        updated_file_contents = apply_stemplate(file_contents, Params(test_variables))

        # test that the correct neighborhood got rendered into the file contents
        render_check = "capital-hill" in updated_file_contents

        self.assertTrue(render_check)

