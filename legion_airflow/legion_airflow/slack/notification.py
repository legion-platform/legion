#
#    Copyright 2018 IQVIA
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
"""
Notifications to slack.
"""

import re
from slackclient import SlackClient
from airflow import configuration
from airflow.exceptions import AirflowConfigException
from airflow.utils.log.logging_mixin import LoggingMixin


def send_notification(receiver, subject, html_content, **kwargs):
    """
    Send Slack notification using configuration from config file.

    :param receiver: email receiver, used to implement signature
    :param subject: email receiver, used to implement signature
    :param: html_content: message content, typically html format is used
    :return:
    """
    _ = receiver
    _ = subject
    _ = kwargs

    log = LoggingMixin().log

    try:
        token = configuration.conf.get('slack', 'TOKEN')
        channel = configuration.conf.get('slack', 'CHANNEL')
        username = configuration.conf.get('slack', 'USERNAME')
        for value in (token, channel, username):
            if not value:
                raise AirflowConfigException("error: empty value")
    except AirflowConfigException:
        log.info("No token/channel/username found for slack.")
        return

    send_notification_to_channel(format_message(html_content),
                                 channel, token, username)


def send_notification_to_channel(message, channel, token, username):
    """
    Send message to Slack channel using token.

    :param message: notification content
    :param channel: slack channel
    :param token: slack token
    :param username: slack username
    :return:
    """
    slack_client = SlackClient(token)
    slack_client.api_call('chat.postMessage', channel=channel,
                          text=message, username=username,
                          icon_emoji=':robot_face:')


def format_message(text):
    """
    Format html message to adopt it for Slack.

    :param: text: html formatted text
    :return: slack formatted text
    """
    text_without_br = re.sub('<br>', '\n', text)
    text_with_fixed_links = re.sub(r"<a href='([^']+)'>([^>]+)</a>",
                                   r"<\1|\2>", text_without_br)

    return text_with_fixed_links
