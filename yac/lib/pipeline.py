#!/usr/bin/env python
import boto3, jmespath, time, os, copy, sys, datetime
from math import ceil
from yac.lib.repo import clone_repo
from yac.lib.search import search
from yac.lib.stage import Stage
from yac.lib.logger import get_deploy_logger
from yac.lib.notification import Notifications
from yac.lib.schema import validate

class Pipeline():

    def __init__(self,
                 serialized_pipeline):

        # first validate. this should throw an exception if
        # required fields aren't present
        validate(serialized_pipeline,
                 "yac/schema/pipeline.json")

        self.deploy_branch = jmespath.search('"deploy-branch"',
                                              serialized_pipeline)

        self.rollback_branch = jmespath.search('"rollback-branch"',
                                              serialized_pipeline)

        self.setup  = jmespath.search('setup',
                                      serialized_pipeline)

        self.notifications = search('notifications',serialized_pipeline)

        self.stages = search('stages',serialized_pipeline,[])

        self.stage_names = search('stages[*].name',serialized_pipeline,[])

    def get_stages(self):
        return self.stages

    def get_logs_path(self, service_alias):

        home = os.path.expanduser("~")

        logs_path = os.path.join(home,'.yac','deploy-logs')

        # save results under /tmp
        timestamp = "{:%Y-%m-%d.%H.%M.%S}".format(datetime.datetime.now())

        logs_full_path = os.path.join(logs_path,'%s.%s'%(service_alias,timestamp))

        return logs_full_path

    def deploy(self,
           service,
           stage_names=[],
           dry_run_bool=False,
           log_level = "INFO"):

        err = ""
        self.log_level = log_level
        self.dry_run = dry_run_bool

        self.service_alias = service.get_description().get_alias()

        self.logs_path = self.get_logs_path(self.service_alias)

        self.logger = get_deploy_logger(self.logs_path,
                                        self.log_level)

        self.notifier = Notifications(self.notifications,
                                      self.logger)

        if not self.stages:
            self._warning("service lacks pipeline stages. exiting")
            exit(1)

        # notify the start of the deploy
        self._info("deploy is begining")

        # build any artifacts associated with this service
        artifacts = service.get_artifacts()

        # make all the artifacts
        # note: for artifacts, we don't want all params (because artifact should
        # not be dependent any of the meta-params, e.g. inputs, service secrets,
        # service build context, etc))
        err = artifacts.make(service.get_params(),
                             service.get_vaults(),
                             artifact_name="",
                             dry_run_bool=dry_run_bool)

        if err:
            self._warning("artifact creation failed with err: %s. exiting"%err)
            exit(1)

        if not stage_names:
            # deploy all stages
            stage_names = self.stage_names

        # for each stage requested
        for stage_name in stage_names:

            # get stage details
            stage,err = self._get_stage(stage_name,
                                        service)

            if not err:
              self._info("running stage '%s'"%stage_name)
              stage.run(dry_run_bool)
            else:
              self._warning("stage '%s' does not exist"%stage_name)

        # notify the completion of the deploy
        self._info("deploy is complete")

    def _info(self,msg):

        # append the service name to give the msg some
        # context
        contextual_msg = "Info from deploy of '%s' service, msg: %s"%(self.service_alias,msg)
        self.notifier.info(contextual_msg)

    def _warning(self,msg):

        # append the service name to give the msg some
        # context
        contextual_msg = "Warning from deploy of '%s' service: msg: %s"%(self.service_alias,msg)
        self.notifier.warning(contextual_msg)

    def _get_stage(self, stage_name, service):

        search_syntax = "[?name=='%s'] | [0]"%stage_name
        this_stage = jmespath.search(search_syntax,
                                     self.stages)

        err = ""
        if this_stage:
          return Stage(this_stage,
                       service,
                       self.notifier,
                       self.logger),err
        else:
          err = "stage %s does not exist"%stage_name
          return None,err