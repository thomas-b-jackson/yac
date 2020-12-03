import unittest, os, random
from yac.lib.notifier.slack import SlackNotifier

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # api token is per yac-notifications-testing user in the
        # following slack site: https://yac-workspace.slack.com
        # for tests to succeed, user needs the following scope:
        #   * write messages
        #   * upload files
        cls.api_key = "xoxp-298418519346-299477551335-298940186947-9efc21317fda08864fbd374f5dffd719"

    def test_info(self):

        slack_config = {
            "info-channel": "info",
            "warning-channel": "warnings",
            "api-key": TestCase.api_key
        }

        slack = SlackNotifier(slack_config)

        slack.info("testing")

        self.assertTrue(True)

    def test_info_w_file(self):

        slack_config = {
            "info-channel": "info",
            "warning-channel": "warnings",
            "api-key": TestCase.api_key
        }

        slack = SlackNotifier(slack_config)

        slack.info("here are some sources!","yac/lib/notification.py")

        self.assertTrue(True)

    def test_bad_file(self):

        slack_config = {
            "info-channel": "info",
            "warning-channel": "warnings",
            "api-key": TestCase.api_key
        }

        slack = SlackNotifier(slack_config)

        slack.info("this file doesn't exist!","yac/lib/gibberish.py")

        self.assertTrue(True)

    def test_warning(self):

        slack_config = {
            "info-channel": "info",
            "warning-channel": "warnings",
            "api-key": TestCase.api_key
        }

        slack = SlackNotifier(slack_config)

        slack.warning("testing")

        self.assertTrue(True)
