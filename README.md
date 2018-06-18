# Retrospective Bot

Retrospective Bot is a Slack bot that records 'Good', 'Bad' and 'Try' items for the retrospective of the current scrum sprint in an Airtable table.

It is a simple web app designed to be used as a [Slack integration](https://slack.com/integrations). Specifically, it responds to POSTs created by the Slack *Slash Commands* integration and responds with messages to Slack's *Incoming Webhooks* integration.

![DemoGif](static/retrospective-bot-demo.gif)

#### Deploy Retrospective Bot

Retrospective Bot is a [Flask](http://flask.pocoo.org/) app built to run on [AWS Lambda](http://docs.aws.amazon.com/lambda/latest/dg/welcome.html).

#### Set Up on Slack

Retrospective Bot uses two Slack integrations: [Slash Commands](https://api.slack.com/slash-commands) for private communication between the bot and the user, and [Incoming Webhooks](https://api.slack.com/incoming-webhooks) for posting public messages.

[Set up a Slash Command integration](https://my.slack.com/services/new/slash-commands). There are three critical values that you need to set or save: **Command** is the command people on Slack will use to communicate with the bot. We use `/retro`. **URL** is the public URL where the bot will live; **LEAVE THIS PAGE OPEN** so that you can fill this in after you've deployed the application to AWS Lambda, as described below. **Token** is used to authenticate communication between Slack and the bot; save this value for when you're setting up the bot on AWS Lambda.

[Set up an Incoming Webhooks integration](https://my.slack.com/services/new/incoming-webhook). The first important values here is **Post to Channel**, which is a default channel where public messages from the bot will appear. This default is always overridden by the bot, but you do need to have one – we created a new channel called *#retrospective-bot* for this purpose. Save the value of **Webhook URL**; this is the URL that the bot will POST public messages to, and you'll need it when setting up Retrospective Bot on AWS Lambda.

#### Deploy on AWS Lambda

Paste the **Token** from the Slash Command integration into the `SLACK_TOKEN` field and the **Webhook URL** from the Incoming Webhooks integration into the `SLACK_WEBHOOK_URL` field.
Copy that URL, paste it into the **URL** field of the Slash Command integration page on Slack, and save the integration there.

And now you're good to go! Open up Slack and type `/retro help` to start.

# Setup
 
* Install docker and docker-compose.
* Checkout this code on your machine.
* Run Zappa to deploy this code as a AWS Lambda function: `docker-compose run --rm deploy zappa deploy dev`. For more info about how Zappa works [check its documentation](https://github.com/Miserlou/Zappa).
* [Add a new webhook in Github](https://github.com/bayesimpact/paul-emploi/settings/hooks). Enter the url of your freshly created AWS Lambda endpoint, use 'json' for the Content type, and select the individual event 'Issue Comment'.
* Get a personal auth token on Github, then add it as GITHUB_PERSONAL_ACCESS_TOKEN to the [AWS Lambda function environment variables](https://console.aws.amazon.com/lambda/home) to your local machine if you want to test this code locally.
 
# Lint and Test
If you want to modify this code:
 
* To test the Flask endpoint of the AWS Lambda function locally:
```
docker-compose run --rm test bash
FLASK_APP=reviewable_to_slack.py flask run &
curl -H "Content-Type: application/json" -X POST --data @github_notification_payload_example.json http://127.0.0.1:5000/handle_github_notification
```
* To run the linting and testing:
```
docker-compose run --rm test ./lint_and_test.sh`.
```
* To deploy your new code on AWS Lambda:
```
docker-compose run --rm deploy
zappa update dev
# To get the live debug logs:
zappa tail
```
