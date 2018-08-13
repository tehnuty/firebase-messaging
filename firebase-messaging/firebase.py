import json

import datetime
import logging
import requests

import firebase_admin
from firebase_admin import messaging, credentials

# To make it work locally, uncomment this:
# from requests_toolbelt.adapters import appengine
# appengine.monkeypatch()

class ApiCallError(Exception):
    """Represents an Exception encountered while invoking the ID toolkit API."""

    def __init__(self, code, message, error=None):
        Exception.__init__(self, message)
        self.code = code
        self.detail = error


class PushActions(object):
    # Opens app on default view
    OPEN_APP = '1'
    # Opens app and navigates to deep_link ("url")
    OPEN_DEEP_LINK = '2'
    # Silent update account
    SILENT_UPDATE_ACCOUNT = '3'


def _initialize_firebase():
    firebase_secrets = "SECRETS"
    cred = credentials.Certificate(firebase_secrets)
    if (not len(firebase_admin._apps)):
        firebase_admin.initialize_app(cred, {"projectId": "PROJECT_ID"})

def _get_topics_by_token(push_token):
    """
    :param push_token: required
    :return: topics, to which this token is subscribed (tags)
    """
    firebase_server_key = "SERVER_KEY"
    firebase_info_url = "FIREBASE_INFO_URL" # "https://iid.googleapis.com/iid/info/"

    auth_key = "key=%s" % firebase_server_key

    headers = {
        "Authorization": auth_key
    }

    url = firebase_info_url + push_token + '?details=true'
    response = requests.get(url, headers=headers)
    response_dict = json.loads(response.text)
    return response_dict['rel']['topics'].keys()

def refresh_subscription(push_token, topics):
    """
    1. Initialize firebase
    2. find tags to add / remove
    3. update
    :param push_token: required
    :param topics: tagObjs
    :return:
    """
    _initialize_firebase()
    try:
        followed_tags = _get_topics_by_token(push_token)
    except:
        followed_tags = []

    new_tags = [topic for topic in topics if topic not in followed_tags]
    old_tags = [topic for topic in followed_tags if topic not in topics]
    for topic in new_tags:
        try:
            messaging.subscribe_to_topic([push_token], topic)
            logging.info("Topic %s added to %s" % (topic, push_token))
        except:
            logging.error("Could not subscribe %s to %s" % (push_token, topic))

    for topic in old_tags:
        try:
            messaging.unsubscribe_from_topic([push_token], topic)
            logging.info("Topic %s removed from %s" % (topic, push_token))
        except:
            logging.error("Could not unsubscribe %s from %s" % (topic, push_token))
    return


def send_notification(push_token=None, push_topic=None, title=None, body=None, url=None, action=None, group_id=None, device_id=None, silent=False):
    """
    :param push_token: optional this or push_topic
    :param push_topic: optional this or push_token
    :param title: notification title
    :param body: notification body message
    :param url: deeplink
    :param action: actions (1. open app, 2. deep link, 3. silent push)
    :param group_id: notification ID (if you want to override notification) e.g. afs:Card:001
    :param device_id: device id of sender (so it wont silent push itself and start an infinity loop)
    :param silent: if push is silent or notification
    :return: firebase response
    """
    _initialize_firebase()

    silent = str(silent)

    if action is PushActions.OPEN_APP:
        payload = {
            "title": title,
            "body": body,
            "action": action,
            "groupId": group_id,
            "silent": silent,
        }
    elif action is PushActions.OPEN_DEEP_LINK:
        payload = {
            "title": title,
            "body": body,
            "url": url,
            "action": action,
            "groupId": group_id,
            "silent": silent,
        }
    elif action is PushActions.SILENT_UPDATE_ACCOUNT:
        payload = {
            "action": action,
            "deviceId": device_id,
            "silent": silent
        }
    if push_token:
        message = messaging.Message(
            android=messaging.AndroidConfig(
                ttl=datetime.timedelta(seconds=3600),
                priority='normal',
                data=payload
            ),
            token=push_topic,
        )

    elif push_topic:
        message = messaging.Message(
            android=messaging.AndroidConfig(
                ttl=datetime.timedelta(seconds=3600),
                priority='normal',
                data=payload
            ),
            topic=push_topic,
        )

    # Send a message to devices subscribed to the combination of topics
    # specified by the provided condition.
    response = messaging.send(message)
    return response