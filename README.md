<h1 align="center"><img alt="Opus Bot" title="Opus Bot" src=".github/logo.png" width="250" /></h1>

# Opus Bot

## 💡 Project's Idea

This project was developed to create a Telegram Chatbot to help people enhance their prayers life.

[Access it live on Telegram](https://t.me/renato_henz_bot)

## 🔍 Features

* Request common prayers;
* Register services to receive prayers periodically;

## 🛠 Technologies

During the development of this project, the following techologies were used:

- [Python](https://www.python.org/)
- [Telegram Bots](https://core.telegram.org/bots)
- [Advanced Python Scheduler](https://apscheduler.readthedocs.io/en/3.x/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [AWS S3](https://aws.amazon.com/pt/s3/)
- [AWS DynamoDB](https://aws.amazon.com/pt/dynamodb/)

## 💻 Project Configuration

### First, create a new virtual environment on the root directory

```bash
$ python -m venv env
```

### Activate the created virtual environment

```bash
$ .\env\Scripts\activate # On Windows machines
$ source ./env/bin/activate # On MacOS/Unix machines
```

### Install the required packages/libs

```bash
(env) $ pip install -r requirements.txt
```

## 🌐 Setting up config files

Create an *.env* file on the root directory, with all needed variables, credentials and API keys, according to the sample provided (*example.env*).

## ⏯️ Running

To run the project in a development environment, execute the following command on the root directory, with the virtual environment activated.

```bash
(env) $ python run.py
```

The *opus-bot.service* file must be updated and placed in the '/etc/systemd/system/' directory. After that, you should execute the following commands to enable and start the service:

```bash
$ sudo systemctl daemon-reload
$ sudo systemctl enable opus-bot
$ sudo systemctl start opus-bot
$ sudo systemctl status opus-bot
```

In order to leave the virtual environment, you can simply execute the command below:

```bash
(env) $ deactivate
```

### 👀 Observations

The website [Hablar con Dios, Francisco Fernández-Carvajal](https://www.hablarcondios.org/pt/meditacaodiaria.aspx), from where we retrieve the daily meditations, has a few security restrictions. Therefore, sometimes, it might not be possible to retrieve the daily meditation.

### Documentation:
* [Church Calendar API](http://calapi.inadiutorium.cz/api-doc)
* [Telegram Bot API](https://core.telegram.org/bots/api)
* [Gangsta: A Telegram Chatbot with Python from scratch](https://www.youtube.com/watch?v=5nhdxpoicW4&ab_channel=SouravJohar)
* [gangsta](https://github.com/SouravJohar/gangsta)
* [Learn to build your first bot in Telegram with Python](https://www.freecodecamp.org/news/learn-to-build-your-first-bot-in-telegram-with-python-4c99526765e4/)
* [Building a Chatbot using Telegram and Python (Part 1)](https://www.codementor.io/@garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay)
* [configparser — Configuration file parser](https://docs.python.org/3/library/configparser.html)
* [Running Pip3 ImportError: cannot import name 'main'](https://askubuntu.com/questions/1025793/running-pip3-importerror-cannot-import-name-main)
* [Automating Python Scripts with Systemd: A Step-by-Step Guide](https://tecadmin.net/setup-autorun-python-script-using-systemd/)
* [python-telegram-bot - Code snippets](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets)
* [telegram.ext package](https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.html)
* [Emoji Cheat Sheet](https://www.webfx.com/tools/emoji-cheat-sheet/)
* [User guide - APScheduler](https://apscheduler.readthedocs.io/en/latest/userguide.html)
* [apscheduler.triggers.cron — APScheduler 3.9.0.post1.post1 documentation](https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html)

## 📄 License

This project is under the **MIT** license. For more information, access [LICENSE](./LICENSE).
