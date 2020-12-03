#!/usr/bin/env python
import time, os, copy, sys, datetime
from math import ceil
from yac.lib.module import get_module
from yac.lib.search import search
from yac.lib.calcs import clear_calc_cache

class Stage():

    def __init__(self,
                 serialized_stage,
                 service,
                 notifier,
                 logger):

        # first validate. this should throw an exception if
        # required fields aren't present
        # validate("yac/schema/stage.json")

        self.service = service

        self.setup = search('setup',serialized_stage,"")

        self.name = search('name',serialized_stage,"")

        self.build_context = search('"build-context"',serialized_stage,"")

        self.kvps = search('kvps',serialized_stage,"")

        self.credentialer_names = search('creds',serialized_stage,"")

        self.params_file = search('"params-file"',
                                  serialized_stage,"")

        self.task_names = search('tasks',
                            serialized_stage,[])

        self.test_names = search('tests',
                            serialized_stage,[])

        self.group_names = search('"test-groups"',
                            serialized_stage,[])

        self.confirmation_prompt = search('"confirmation-prompt"',
                                    serialized_stage,"")

        self.start_time = search('"start-time"',
                                    serialized_stage,"")

        self.cleanup = search('cleanup',
                             serialized_stage,"")

        self.notifier = notifier

        self.logger = logger

    def run(self, dry_run_bool):

        self.dry_run_bool = dry_run_bool

        # honor any specified start times
        self._delay_start()

        # load kvps specific to this stage
        self.service.params.load_kvps(self.kvps)

        # get all params for this context
        self.params = self.service.get_all_params(self.build_context,
                                             dry_run_bool,
                                             self.credentialer_names)

        # generate credentials appropriate to this stage
        credentialers = self.service.get_credentialers()

        if credentialers and self.credentialer_names:

            for credentialer_name in self.credentialer_names:

                # in pipeline mode, always overwrite any existing credentials file
                err = credentialers.create(credentialer_name,
                                           self.params,
                                           self.service.get_vaults(),
                                           overwrite_bool=True)
                if err:
                    break

        # clear any yac-calc caches
        clear_calc_cache(self.params)

        # build the stack associate with this service
        err = self._build_stack()

        if err:
            self._warning("stack update failed with err: %s. aborting deploy"%err)
            exit(1)

        # run tasks against the built service
        err = self._run_tasks()

        if err:
            self._warning("task execution failed with err: %s. aborting deploy"%err)
            exit(1)

        # run integration tests against the built service
        test_status = self._run_tests()

        # if the tests failed, abandon deploy
        if test_status == 1:
            self._warning("integration testing failed. aborting deploy")
            exit(1)

        if self.confirmation_prompt:
            # notify that manual confirmation is pending
            self._info("stage '%s' is complete. continue?"%(stage_name))
            input()

    def _build_stack(self):

        self._info("beginning stack updates")

        err = ""

        # get the stack associated with the service
        self.stack = self.service.get_stack()

        if self.stack:

            # build the stack
            err = self.stack.build(self.params,
                                   deploy_mode_bool=True,
                                   dry_run_bool=self.dry_run_bool,
                                   context=self.build_context)

        return err

    def _run_tasks(self):

        err = ""

        # get the tasks associated with this service
        tasks = self.service.get_tasks()

        for task_name in self.task_names:

            # verify task is available
            if tasks.get(task_name):

                # run this task
                if not self.dry_run_bool:

                    self._info("running task %s against stack"%task_name)
                    err = tasks.run(task_name,
                                    self.params)

                    if err:
                        break
                else:
                    self._info("task '%s' skipped (tasks not run in deploy dry runs)"%task_name)
            else:
                err = "task %s is not available"%task_name

        return err

    def _run_tests(self):

        err = ""

        # get all integration tests
        integration_tests = self.service.get_tests()

        if integration_tests:

            if not self.dry_run_bool:

                self._info("starting integration testing")

                # run the tests
                integration_tests.run(self.params,
                                      self.build_context,
                                      self.test_names,
                                      self.group_names)

                # save test results to results store
                integration_tests.save_test_results()

                test_results = integration_tests.get_results()

                # process test results
                err = test_results.process()

            else:
                self._info("integration testing skipped (tests not run in deploy dry runs)")

        return err

    def _run_setup(self):

        if self.setup:

            module, err = get_module(self.setup,
                                self.service_parameters)

            if not err:
                if hasattr(module,'setup_deploy'):

                    # call the setup_deloy fxn in the module
                    err = module.setup_deploy(self.service_parameters)
                else:

                    msg = ("setup module %s "%self.setup +
                           " does not have a 'setup_deploy' function")
            if err:
                self.logger.error(msg)

    def _run_cleanup(self):

        if self.cleanup:

            module, err = get_module(self.cleanup,
                                self.service_parameters)

            if not err:

                if hasattr(module,'cleanup_deploy'):

                    # call the cleanup_deploy fxn in the module
                    err = module.cleanup_deploy(self.service_parameters)
                else:

                    msg = ("cleanup module %s "%self.cleanup +
                           " does not have a 'cleanup_deploy' function")

            if err:
                self.logger.error(msg)

    def _delay_start(self):

        if self.start_time:

            time_parts = self.start_time.split(":")

            # calculate the future date/time relative to today
            now = datetime.datetime.today()
            deploy_start = datetime.datetime(now.year,
                                             now.month,
                                             now.day,
                                             int(time_parts[0]),
                                             int(time_parts[1]))

            deploy_start_delay_sec = (deploy_start-now).seconds

            delay_min = int(ceil(float(deploy_start_delay_sec)/60))
            self._info("deploy will start at: %s"%time_str)
            self._info("start delayed for %s minutes"%str(delay_min))

            # sleep for 1 minute at a time, and recheck current time
            # against deploy time before resuming sleep
            while now.seconds < deploy_start.seconds:

                # 15 minutes prior to the start time, send
                # a "deploy imminent" notification
                warning_start_delay_sec = (deploy_start-now).seconds-15*60

                if ( deploy_start - now ).seconds < 15*60 :

                    self._info("deploy will start in 15 minutes!")

                # sleep for another minute
                time.sleep(60)

                # update now for use in while loop logic
                now = datetime.datetime.today()

    def _info(self,msg):

        # append the stage name to give the msg some
        # context
        contextual_msg = "Info from stage: %s, msg: %s"%(self.name,msg)
        self.notifier.info(contextual_msg)

    def _warning(self,msg):

        # append the stage name to give the msg some
        # context
        contextual_msg = "Warning from stage: %s, msg: %s"%(self.name,msg)
        self.notifier.warning(contextual_msg)

