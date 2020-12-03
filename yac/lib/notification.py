#!/usr/bin/env python

import jmespath, os, io
from yac.lib.logger import get_yac_logger
from yac.lib.notifier.slack import SlackNotifier
from yac.lib.notifier.stdout import StdOutNotifier

class Notifications():

    def __init__(self,
                notification_descriptor,
                logger=None):

        notification_type = jmespath.search('type',
                                              notification_descriptor)

        if notification_type == 'slack':

            slack_configs = jmespath.search('configs',
                                              notification_descriptor)

            self.impl = SlackNotifier(slack_configs,
                                      logger)

        else:
            self.impl = StdOutNotifier(logger)

    def info(self,msg,file_path=""):
        self.impl.info(msg,file_path)

    def warning(self,msg,file_path=""):
        self.impl.warning(msg,file_path)