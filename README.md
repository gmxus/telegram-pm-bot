# telegram-pm-bot
concatnate your conversation between the bot and the sender.

based on [telegram-pm-chat-bot](https://github.com/Netrvin/telegram-pm-chat-bot).


## Installation
firstly prepared the following:
- python 2
- pip

then run :
```bash
pip install python-telegram-bot --upgrade
```


## Config
modify those on `/config.json` :
```json
{
    "Admin": 0,        // ID of admin account (number id)
    "Token": "0",      // Token of bot
    "Lang": "en"       // name of the lang file
}
```


## Start
```bash
python main.py
```


## Directive
| command         | function                                  | parameter                                  |
| :---            | :---                                      | :---                                       |
| receipt_switch  | enable or disable receipt                 | /receipt_switch                            |
| messege_info    | info of the messege you point             | /messege_info                              |
| say             | start conversation                        | /say                                       |
| done            | end conversation                          | /done                                      |
| version         | version of bot                            | /version                                   |
