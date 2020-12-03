from yac.lib.notifier.notifier import Notifier

class StdOutNotifier(Notifier):

    def __init__(self,
                 logger):

        self.logger = logger

    def info(self,msg,file_path=""):

        self.logger.info(msg)

    def warning(self,msg,file_path=""):

        self.logger.warning(msg)