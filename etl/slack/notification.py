#
#    Copyright 2017 EPAM Systems
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

from airflow import configuration
from slackclient import SlackClient


def send_notification(receiver, subject, html_content):
    """
    Send Slack notification using configuration from config file.

    :param receiver: email receiver, used to implement signature
    :param subject: email receiver, used to implement signature
    :param: html_content: message content, typically html format is used
    :return:
    """
    _ = receiver
    _ = subject

    token = configuration.conf.get('slack', 'TOKEN')
    channel = configuration.conf.get('slack', 'CHANNEL')
    username = configuration.conf.get('slack', 'USERNAME')

    send_notification_to_channel(html_content, channel, token, username)


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
