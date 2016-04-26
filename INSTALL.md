# Installing Glossary Bot Locally

Follow these instructions to install a copy of Glossary Bot locally for development and testing.

#### Requirements

Glossary Bot is written in Python 2.7.

#### Install

Glossary Bot is a [Flask](http://flask.pocoo.org/) app built to run on [Heroku](https://heroku.com/).

To install locally, clone this repository and cd into the resulting directory:

```
git clone git@github.com:bayesimpact/retrospective-bot.git
cd retrospective-bot
```

Set up and activate a new virtual environment using [Virtualenv](https://github.com/codeforamerica/howto/blob/master/Python-Virtualenv.md):

```
virtualenv venv-retrospective-bot
```

Activate the virtual environment:

```
source venv-retrospective-bot/bin/activate
```

Install the required packages with pip:

```
pip install -r requirements.txt
```

Create the production [PostgreSQL](https://github.com/codeforamerica/howto/blob/master/PostgreSQL.md) database:

```
createdb retrospective-bot
```

Copy `env.sample` to `.env`:

```
cp env.sample .env
```

and make sure that the value of `DATABASE_URL` in `.env` matches the name of the database you created in the last step.

Initialize the database:

```
python manage.py db upgrade
```

And run the application:

```
python manage.py runserver
```

#### Test

To run the app's tests, first create a test database. Make sure the name of the database matches the value of `environ['DATABASE_URL']` set in the `setUp()` function in [test/test_bot.py](https://github.com/bayesimpact/retrospective-bot/blob/master/tests/test_bot.py):

```
createdb retrospective-bot-test
```

You can now run the tests from the command line:

```
python manage.py runtests
```

or run an individual test:

```
python tests/test_bot.py TestBot.test_get_definition
```
