class Notifier():
    # base class for all pipeline notifiers (slack, std, etc)

    def info(self,msg,file_path=""):
        print(msg)

    def warning(self,msg,file_path=""):
        print(warning)