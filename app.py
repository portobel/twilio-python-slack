import datetime
import logging
import os
import slack
import re
from dotenv import load_dotenv
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()
app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

thread_history_length_days = int(os.getenv("THREAD_HISTORY_LENGTH_DAYS"))
message_channel = os.getenv("SLACK_CHANNEL_NAME")
channel_id = os.getenv("SLACK_CHANNEL_ID")
icon_emoji = os.getenv("SLACK_ICON_EMOJI")
slack_token = os.getenv("SLACK_BOT_TOKEN")
two_way_enabled = os.getenv("TWO_WAY_COMMUNICATION_ENABLED").lower() in ['true', '1', 't', 'y', 'yes']
auto_reply_message = os.getenv("AUTO_REPLY_MESSAGE")

slack_client = slack.WebClient(slack_token)
twilio_client = Client()


# Uncomment next line to log request contents
@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())


def find_parent_message(from_number: str):
    try:
        oldest = datetime.datetime.today() - datetime.timedelta(days=thread_history_length_days)
        response = slack_client.conversations_history(channel=channel_id, limit=500, oldest=oldest.timestamp())
        for message in response['messages']:
            if from_number in message['text']:
                return message['ts']
    except Exception as e:
        app.logger.error('Error while trying to find corresponding thread in Slack for ' + from_number + ': ' + str(e))

    return None


@app.route('/incoming/twilio', methods=['POST'])
def send_incoming_message():
    from_number = request.form['From']
    sms_message = request.form['Body']
    message = f"Message from {from_number}: {sms_message}"

    ts = find_parent_message(from_number)
    slack_client.chat_postMessage(
        channel=message_channel, text=message, icon_emoji=icon_emoji, thread_ts=ts)

    if auto_reply_message and not ts:
        try:
            twilio_client.messages.create(
                to=from_number, from_=os.getenv("TWILIO_NUMBER"), body=auto_reply_message)
        except Exception as e:
            app.logger.error('Error in sending autoresponse for ' + from_number + ' via Twilio: ' + str(e))

    response = MessagingResponse()
    return Response(response.to_xml(), mimetype="text/html"), 200


@app.route('/incoming/slack', methods=['POST'])
def send_incoming_slack():
    if not two_way_enabled:
        return Response(), 200

    attributes = request.get_json()
    if 'challenge' in attributes:
        return Response(attributes['challenge'], mimetype="text/plain")
    incoming_slack_message_id, slack_message, channel = parse_message(attributes)
    if incoming_slack_message_id and slack_message:
        to_number = get_to_number(incoming_slack_message_id, channel)
        if to_number:
            automated = f"Message from {to_number}:"
            if not slack_message.startswith(automated):
                twilio_client.messages.create(
                    to=to_number, from_=os.getenv("TWILIO_NUMBER"), body=slack_message)
        return Response(), 200
    return Response(), 200


def parse_message(attributes):
    if 'event' in attributes and 'thread_ts' in attributes['event']:
        return attributes['event']['thread_ts'], attributes['event']['text'], attributes['event']['channel']
    return None, None, None


def get_to_number(incoming_slack_message_id, channel):
    data = slack_client.conversations_history(channel=channel, latest=incoming_slack_message_id, limit=1, inclusive=1)
    if 'subtype' in data['messages'][0] and data['messages'][0]['subtype'] == 'bot_message':
        text = data['messages'][0]['text']
        phone_number = extract_phone_number(text)
        return phone_number
    return None


def extract_phone_number(text):
    data = re.findall(r'\+\d+', text)
    if len(data) >= 1:
        return data[0]
    return None


if __name__ == '__main__':
    app.run(threaded=True)
