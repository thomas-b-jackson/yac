import os
from yac.lib.search import search
from yac.lib.module import get_module
from yac.lib.inputs import Inputs
from yac.lib.schema import validate

class Tasks():

    def __init__(self,
                 serialized_tasks):

        # first validate. this should raise an error if
        # required fields aren't present
        validate(serialized_tasks,
                 "yac/schema/tasks.json")

        self.values = {}
        for serialized_task in serialized_tasks:

            this_task = Task(serialized_task)
            self.values[this_task.name] = this_task

    def add(self, tasks):

        self.values.update(tasks.values)

    def get_names(self):

        return list(self.values.keys())

    def get(self,task_name):

        if task_name in list(self.values.keys()):
            return self.values[task_name]
        else:
            return None

    def run(self,
            task_name,
            params):

        self.params = params

        if task_name in list(self.values.keys()):

            return self.values[task_name].run(params)

        else:
            return "requested task does not exist"

class Task():

    def __init__(self,
                 serialized_task):

        self.name = search("name",serialized_task,"")
        self.description = search("description", serialized_task,"")
        self.module = search("module",serialized_task,"")
        self.inputs = Inputs(search("Inputs", serialized_task, {}))

    def run(self, params):

        err = ""
        self.params = params

        servicefile_path = self.params.get('servicefile-path')

        # process task inputs and load results into params
        self.inputs.load(self.params)

        task_module, err = get_module(self.module, servicefile_path)

        # run the handler method in the task module
        if not err:
            if hasattr(task_module,'task_handler'):
                err = task_module.task_handler(self.params)
            else:
                err = ("task module %s does not have a " +
                       "'test_setup' function"%self.module)

        return err
