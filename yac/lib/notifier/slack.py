import os, io
from slackclient import SlackClient
from yac.lib.notifier.notifier import Notifier
from yac.lib.search import search
from yac.lib.logger import get_yac_logger
from yac.lib.schema import validate

class SlackNotifier(Notifier):

    def __init__(self,
                 notifier_descriptor,
                 logger=None):

        # first validate. this should throw an exception if
        # required fields aren't present
        validate(notifier_descriptor,
                 "yac/schema/notifier/slack.json")

        self.info_channel  = search('"info-channel"',
                                    notifier_descriptor,"")
        self.warning_channel = search('"warning-channel"',
                                    notifier_descriptor,"")

        self.api_key = search('"api-key"',
                                notifier_descriptor,"")

        self.client = SlackClient(self.api_key)

        if logger:
            self.logger = logger
        else:
            self.logger = get_yac_logger()

    def info(self,msg,file_path=""):

        if not file_path:

            # send msg to slack
            self.client.api_call(
                "chat.postMessage",
                channel=self.info_channel,
                text=msg)

            # also send msg to stdout
            self.logger.info(msg)

        else:

            # send file to slack
            self.send_file(self.info_channel,
                           msg,
                           file_path)

    def warning(self,msg,file_path=""):

        if not file_path:

            self.client.api_call(
                "chat.postMessage",
                channel=self.warning_channel,
                text=msg)

            # also send msg to stdout
            self.logger.warning(msg)
        else:

            self.send_file(self.warning_channel,
                           msg,
                           file_path)

    def send_file(self,
                  channel,
                  msg,
                  file_path):

        if os.path.exists(file_path):
            content = ""
            with open(file_path, 'r') as myfile:
                content=myfile.read()

            if content:

                filename = os.path.basename(file_path)

                ret = self.client.api_call("files.upload",
                                           filename=filename,
                                           channels=channel,
                                           file= io.BytesIO(str.encode(content)),
                                           initial_comment=msg)

                if not 'ok' in ret or not ret['ok']:
                    # error
                    self.logger.error('upload of file %s failed with: %s'%(filename,ret['error']))

                self.logger.info("file %s sent to slack"%file_path)
        else:
            self.logger.error("file %s does not exist"%file_path)
