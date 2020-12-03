import unittest, os, io, sys
from yac.lib.task import Tasks
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.serialized_tasks = [
          {
            "name": "backup",
            "description": "take a snapshot backup of the postgres data",
            "module": "lib/backup.py"
          },
          {
            "name": "restore",
            "description": "restore DB from the most recent backup or from a specific point-in-time",
            "module": "yac/tests/tasks/vectors/sample.py",
            "Inputs": [
              {
                "key": "env",
                "title": "Environment",
                "type": "string",
                "help":  "The environment to build stack for",
                "required": True
              }
            ]
          }
        ]

    def test_get_task(self):

        tasks = Tasks(TestCase.serialized_tasks)

        self.assertTrue(tasks and tasks.get('backup') and tasks.get('restore'))

    def test_get_task_module(self):

        tasks = Tasks(TestCase.serialized_tasks)

        self.assertTrue(tasks and tasks.get('restore') and
                        "sample.py" in tasks.get('restore').module)

    def test_get_task_inputs(self):

        tasks = Tasks(TestCase.serialized_tasks)

        self.assertTrue(tasks and tasks.get('restore') and 
                        tasks.get('restore').inputs)

    def test_run_task(self):

        tasks = Tasks(TestCase.serialized_tasks)

        restore_task = tasks.get('restore')

        # inject an response to input prompt
        sys.stdin = io.StringIO("dev")

        params = Params({})
        err = restore_task.run(params)

        self.assertTrue( err == "" )