import unittest, os, random, json
from yac.lib.template import apply_stemplate, apply_ftemplate
from yac.lib.template import apply_templates_in_dir, apply_templates_in_file,TemplateError
from yac.lib.file import get_file_contents
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_stemplate(self):
        # test rendering templates in a string

        test_variables = {
            "user-name": {"value": "Tom Jaxon"}
        }

        string_w_variables = "Try and render {{yac-ref:user-name}} into this file"

        # run test
        string_w_variables = apply_stemplate(string_w_variables, Params(test_variables))

        # test that user name got rendered into the file contents
        render_check = "Tom Jaxon" in string_w_variables

        self.assertTrue(render_check)

    def test_stemplate_miss(self):
        # test that a non-existant param raises a TemplateError

        test_variables = {
            "user-names": {"value": "Tom Jaxon"}
        }

        string_w_variables = "Try and render {{yac-ref:user-name}} into this file"

        # run test
        error_raised = False
        try:
            apply_stemplate(string_w_variables, Params(test_variables))
        except TemplateError as e:
            error_raised = True
            print(e)

        self.assertTrue(error_raised)

    def test_file_template(self):
        # test rendering templates in a file

        test_file = 'yac/tests/template/vectors/sample_file.txt'

        test_variables = {
            "user-name": {"value": "Tom Jaxon"}
        }

        # run test
        updated_file_contents = apply_ftemplate(test_file, Params(test_variables))

        # test that user name got rendered into the file contents
        render_check = "Tom Jaxon" in updated_file_contents

        self.assertTrue(render_check)

    def test_file_json(self):
        # test rendering templates in a json file containing intrinsics

        test_file = 'yac/tests/template/vectors/render.json'

        test_variables = {
            "latency-sample-period": {"value": 10}
        }

        # run test
        updated_file = apply_templates_in_file(test_file,
                                               Params(test_variables),
                                               "/tmp")

        file_contents = get_file_contents(updated_file)

        updated_file_json = json.loads(file_contents)

        # test that user name got rendered into the file contents
        render_check = updated_file_json["period-mins"]==10

        self.assertTrue(render_check)

    def test_dir_template(self):
        # test rendering templates in a directory

        test_dir = 'yac/tests/template/vectors/sample_dir'

        test_file1 = '/tmp/sample_file1.txt'
        test_file2 = '/tmp/sample_file2.tmp'
        test_file3 = '/tmp/sub_dir/sample_file3.txt'
        test_file4 = '/tmp/sample_binary.xls'

        test_variables = {
            "user-fname": {"value": "Tom"},
            "user-lname": {"value": "Jaxon"}
        }

        # run test
        apply_templates_in_dir(test_dir,
                               Params(test_variables),
                               "/tmp")

        self.assertTrue('Tom Jaxon' in open(test_file1).read())

        self.assertTrue('Tom Jaxon' in open(test_file2).read())

        self.assertTrue('Tom Jaxon' in open(test_file3).read())

        # test to see if binary file copies to destination properly
        self.assertTrue(os.path.exists(test_file4))
