#!/usr/bin/env python3
import os
from typing import Union

from dotenv import load_dotenv, set_key


class ConfigManager:
    def __init__(self):
        self.config = {}
        try:
            load_dotenv(dotenv_path="./.env")
            self.config["DC_TOKEN"] = os.getenv("DISCORD_TOKEN", "")
            self.config["DC_GUILD"] = int(os.getenv("DISCORD_GUILD"))
            self.config["DC_OWNER"] = os.getenv("DISCORD_BOT_OWNER", "")
            self.config["DC_SF_ADMIN_ROLE"] = os.getenv(
                "DISCORD_SF_ADMIN_ROLE", "Ficsit2Discord"
            )
            self.config["SF_IP"] = os.getenv("SF_IP", "127.0.0.1")
            self.config["SF_PORT"] = os.getenv("SF_PORT", "7777")
            self.config["SF_TOKEN"] = os.getenv("SF_TOKEN", "")
            self.config["SF_SERVER_NAME"] = os.getenv(
                "SF_SERVER_NAME", "My awsome server!"
            )
            self.config["SF_PUBLIC_ADDR"] = os.getenv("SF_PUBLIC_ADDR", "127.0.0.1")
            self.config["DC_STATE_CHANNEL"] = os.getenv("DISCORD_STATE_CHANNEL")
        except TypeError as e:
            print(f"Error reading 'dotenv': {e}")

    def get(self, key: str = None) -> Union[int, str, bool]:
        try:
            return self.config[key]
        except KeyError:
            print(f"Error attempting to read unknown configuration key {key}.")
            return False

    def set(self, key: str, value: Union[int, str, bool]) -> bool:
        if isinstance(value, int):
            value = str(value)
        if key is None or value is None:
            raise ValueError(f"Attempt to improperly set config {key=} to {value=}.")
        if isinstance(value, str):
            qm = "always"
            if value.isnumeric():
                if value[:].isdigit():
                    qm = "never"
                else:
                    raise ValueError(
                        f"Attempted to set integer configuration {key} to non-integer {value}."
                    )
        if set_key(
            dotenv_path="./.env", key_to_set=key, value_to_set=value, quote_mode=qm
        ):
            return True
        else:
            return False


def main() -> None:
    import sys

    try:
        raise NotImplementedError("bot_config.py should not be executed directly.")
    except NotImplementedError as e:
        print(f"{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
