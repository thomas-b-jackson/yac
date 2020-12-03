import unittest, os, random
from yac.lib.template import apply_stemplate, apply_ftemplate, apply_templates_in_dir
from yac.lib.template import TemplateError
from yac.lib.file import get_file_contents
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_stranger(self):

        string_w_variables = 'Simons says {{yac-calc:["yac/tests/template/vectors/say_hello.py"]}}'

        # run test
        string_w_variables = apply_stemplate(string_w_variables, Params({}))

        # test that "Hello stranger" got rendered into the string contents
        render_check = "hello stranger" in string_w_variables

        self.assertTrue(render_check)

    def test_named(self):

        string_w_variables = 'Simons says {{yac-calc: ["yac/tests/template/vectors/say_hello.py","godzilla"]}}'

        # run test
        string_w_variables = apply_stemplate(string_w_variables, Params({}))

        # test that "Hello godzilla" got rendered into the string contents
        render_check = "hello godzilla" in string_w_variables

        self.assertTrue(render_check)

    def test_bad_calculator(self):

        string_w_variables = 'Simons says {{yac-calc: ["nonexistent.py"]}}'

        err = ""
        try:
            string_w_variables = apply_stemplate(string_w_variables, Params({}))
        except TemplateError as e:
            err = e

        self.assertTrue(err)