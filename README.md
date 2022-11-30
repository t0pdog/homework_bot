# Homework telegram bot

## Description
The bot uses API Yandex.practicum.
This bot can:
- The bot polls [a endpoint](https://practicum.yandex.ru/api/user_api/homework_statuses/) every 600 seconds and check the status. It must match one of the following:
* approved,
* reviewing,
* rejected.;
- when updating the status, analyze the API response and send you a corresponding notification in Telegram;
- log your work and notify you about important issues with a message in Telegram.

The bot also cheks errors when polling the server and logging.
The bot send message if change status a last homework or detects an error.

### Technology stack is available on requirements.txt

### How to start a project:

Clone a repository and change to it on the command line:
```
git clone https://github.com/t0pdog/homework_bot.git
cd api_yamdb
```

Create and activate virtual environment:
```
python -m venv venv
source venv/Scripts/activate
```

Install dependencies from a file requirements.txt:
```
pip install -r requirements.txt
```
Run the bot:
```
python homework.py
```