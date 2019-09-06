#!/bin/bash
# Deploy the app to AWS Lambda using AWS cli, or environment variables access token.
# TODO(cyrille): Ensure the tests pass beforehand.
# TODO(cyrille): Tag the version both in AWS Lambda and git, to make sure we can link them somehow.

if [ -n "$AWS_SECRET_ACCESS_KEY" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_DEFAULT_REGION" ]; then
    # We have a mean to authenticate to AWS using env, let's use it.
    docker-compose run --rm deploy zappa update dev
    exit 0
fi

if [ -z "$(which aws)" ] || ! [ -x "$(which aws)" ]; then
    # awscli is unavailable.
    echo "No AWS authentification available.
    Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION environment variables or
    install and configure awscli."
    exit 1
fi

docker-compose run --rm deploy
aws --region=us-east-1 lambda update-function-code \
    --function-name slack-retro-bot-to-airtable-dev \
    --zip-file fileb://dist/slack_retro_bot_lambda.zip \
    --publish
