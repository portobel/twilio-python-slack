# twilio-python-slack
A Slack bot for receiving and sending SMS messages using Twilio

Based on this project: https://www.twilio.com/blog/build-sms-slack-bridge-python-twilio

You can have an interactive chat (via Slack) with someone who texts a given Twilio number (and they’ll receive responses via text).
If they (in turn) respond to that response, that response will show up in the thread associated with their number, and the conversation can go on *in the thread* for as long as needed.

This will hold true as long as the conversation is less than *n* days old (where *n* is defined in the environment variable `THREAD_HISTORY_LENGTH_DAYS` below).

All of the below are **required** environment variables. They can be defined in a .env file or as OS environment variables - either will work.

Caveat emptor, there is hardly any error handling or logging in this app at the moment.

```
AUTO_REPLY_MESSAGE=(text for autoreplies, can be left out if no autoreplies are needed)
SLACK_BOT_TOKEN=(required text)
SLACK_CHANNEL_ID=(required text, like C0123456)
SLACK_CHANNEL_NAME=(required text, like #general)
SLACK_ICON_EMOJI=(required text, like :iphone:)
THREAD_HISTORY_LENGTH_DAYS=2 (some integer value like 2)
TWILIO_ACCOUNT_SID=(required text)
TWILIO_AUTH_TOKEN=(required text)
TWILIO_NUMBER=14155551212 (for example, no plus signs or dashes)
TWO_WAY_COMMUNICATION_ENABLED=(not case-sensitive, and any of [true, false, 1, 0, y, n, t, f] will work)
```
