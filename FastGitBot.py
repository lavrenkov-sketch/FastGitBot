import requests
import json
from secrets import compare_digest


class FastGitBot(object):
    def __init__(self, params=None, file=None):
        if file is not None:
            self.load_config(file=file)
        else:
            if params is None:
                params = {}
            self.offset = params.get("offset", 0)
            self.bot_token = params.get(
                "bot_token", "5216005445:AAEhTTbqkuqb9bmY33NIi0Pv1xIn39-RWPbE"
            )
            self.api_url = params.get("api_url", "https://api.telegram.org/bot")
            self.password = params.get("password", "123")
            self.authorized = params.get("authorized", [])
            self.http_proxy = params.get("http_proxy", "")
            self.https_proxy = params.get("https_proxy", "")

    def load_config(self, file="config.json"):
        """
        Read config from file in json format.
        :param file: abspath to file. example "/home/config.json"
        :return: None
        """
        try:
            with open(file) as json_file:
                data = json.load(json_file)
                self.offset = data.get("offset", 0)
                self.bot_token = data.get(
                    "bot_token", "5216005445:AAEhTTbqkuqb9bmYqNIi0Pv1xIn39-RWPbE"
                )
                self.api_url = data.get("api_url", "https://api.telegram.org/bot")
                self.password = data.get("password", "123")
                self.authorized = data.get("authorized", [])
                self.http_proxy = data.get("http_proxy", "")
                self.https_proxy = data.get("https_proxy", "")
        except FileNotFoundError:
            raise FileNotFoundError(
                """
            Missing config file.
            Please set file variable to absolute path.
            Example: read_config(file="\home\config.json
            """
            )

    def save_config(self, file="config.json"):
        """
        Save config to file in json format.
        :param file: abspath to file. example "/home/config.json"
        :return: None
        """
        data = {
            "offset": self.offset,
            "bot_token": self.bot_token,
            "api_url": self.api_url,
            "password": self.password,
            "authorized": self.authorized,
            "http_proxy": self.http_proxy,
            "https_proxy": self.https_proxy,
        }
        with open(file, "w") as outfile:
            json.dump(data, outfile)

    def _call_bot_post(self, metod, params=None):
        if params is None:
            params = {}
        url = f"{self.api_url}{self.bot_token}/{metod}"
        if self.http_proxy or self.https_proxy:
            return requests.post(
                url,
                params,
                proxies={"http": self.http_proxy, "https": self.https_proxy},
            ).json()
        return requests.post(url, params).json()

    def _call_bot_get(self, metod, params=None):
        if params is None:
            params = {}
        url = f"{self.api_url}{self.bot_token}/{metod}"
        if self.http_proxy or self.https_proxy:
            return requests.get(
                url,
                params,
                proxies={"http": self.http_proxy, "https": self.https_proxy},
            ).json()
        return requests.get(url, params).json()

    def _update_offset(self, message):
        """
        Update last readed message id
        :param message: str.
        :return: None
        """
        try:
            self.offset = message["update_id"]+1
        except:
            self.offset = self.offset

    def _check_authorization(self, message):
        """
        Check message for password exists.
        :param message: str.
        :return: None
        """
        if compare_digest(message["message"]["text"], self.password):
            if not message["message"]["from"]["is_bot"]:
                user_id = message["message"]["from"]["id"]
                if user_id not in self.authorized:
                    self.authorized.append(user_id)
                    self.message(text="Congratulations, you add in AllowedList 💸",
                                 chat_id=message["message"]["from"]["id"])
                else:
                    self.message(text="you already in AllowedList.",
                                 chat_id=message["message"]["from"]["id"])
                    self.message(text="😰",
                                 chat_id=message["message"]["from"]["id"])
            else:
                self.message(text="BOT 🥶! Acess denied!", chat_id=message["message"]["from"]["id"])
                self.message(text="🙅", chat_id=message["message"]["from"]["id"])
        else:
            self.message(text="Unknown command", chat_id=message["message"]["from"]["id"])
            self.message(text="💩", chat_id=message["message"]["from"]["id"])


    def read_last_messages(
            self, update_offset=True, check_authorization=True, save_config=True
    ):
        """
        Read all unreaded messages from telegram bot
        :param update_offset: bool. Update readed status of messages ?
        :param check_authorization: bool. Check messages for password authorizations ?
        :param save_config: bool. Save config file after read messages ?
        :return dict. Return request status only if error.
        """
        if update_offset:
            result = self._call_bot_post(
                metod="getUpdates", params={"offset": self.offset}
            )
            if result.get("ok"):
                for one in result.get("result"):
                    self._update_offset(one)
                    if check_authorization:
                        self._check_authorization(one)
            else:
                return result
            if save_config:
                self.save_config()
        return self._call_bot_post(metod="getUpdates", params={"offset": self.offset})

    def message(self, text="Hello !", chat_id=None, parse_mode="Markdown"):
        """
        Send message directly to TelegramBot
        :param text: str. Text to sent.
        :param chat_id: str. Telegram user chat id.
        :param parse_mode: str. Message parse mod.
        :return request status
        """
        if chat_id is not None:
            return self._call_bot_get(
                metod="sendMessage",
                params={"chat_id": chat_id, "parse_mode": parse_mode, "text": text},
            )
        else:
            return 'You not put chat_id in message metod!'

    def message_all(self, text="Hello !", parse_mode="Markdown"):
        """
        Send echo message to all authorized users
        :param text: str. Text to sent.
        :param parse_mode: str. Message parse mod.
        """
        try:
            for one in self.authorized:
                self.message(chat_id=one, text=text, parse_mode=parse_mode)
            return {"status": "ok", "details": "all messages was sent"}
        except Exception as error:
            return {"status": "error", "details": error}

    def loop(self):
        import time
        while True:
            self.read_last_messages(save_config=False)
            time.sleep(3)