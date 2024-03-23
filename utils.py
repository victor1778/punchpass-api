import logging
import re
from datetime import datetime
from typing import Dict, Optional

import pytz

from models import User

NY_TZ = pytz.timezone("America/New_York")
NAME_REGEX = re.compile(r"<[^>]+>")


class CachedList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(__name__)

    def append(self, item):
        if item.id not in [x.id for x in self]:
            self.log.info(f"Adding {type(item).__name__} to schedule_store: {item.id}")
            super().append(item)
        else:
            self.log.info(
                f"Duplicate {type(item).__name__} not added to schedule_store: {item.id}"
            )

    def extend(self, items):
        for item in items:
            if item.id not in [x.id for x in self]:
                self.log.info(
                    f"Adding {type(item).__name__} to schedule_store: {item.id}"
                )
                super().append(item)
            else:
                self.log.info(
                    f"Duplicate {type(item).__name__} not added to schedule_store: {item.id}"
                )

    def __setitem__(self, index, value):
        self.log.info(
            f"Updating {type(value).__name__} in schedule_store at index {index}: {value.id}"
        )
        super().__setitem__(index, value)

    def __delitem__(self, index):
        item = self[index]
        self.log.info(
            f"Removing {type(item).__name__} from schedule_store at index {index}: {item.id}"
        )
        super().__delitem__(index)

    def __iadd__(self, items):
        for item in items:
            if item.id not in [x.id for x in self]:
                self.log.info(
                    f"Adding {type(item).__name__} to schedule_store: {item.id}"
                )
                super().append(item)
            else:
                self.log.info(
                    f"Duplicate {type(item).__name__} not added to schedule_store: {item.id}"
                )
        return self

    def __imul__(self, value):
        self.log.info(f"Multiplying schedule_store by {value}")
        return super().__imul__(value)

    def clear(self):
        self.log.info("Clearing schedule_store")
        super().clear()


class Utils:
    @staticmethod
    def format_cookies(cookie_dict, url) -> list[dict[str, str]]:
        cookies_for_playwright = []
        for name, value in cookie_dict.items():
            cookie = {
                "name": name,
                "value": value,
                "url": url,
            }
            cookies_for_playwright.append(cookie)
        return cookies_for_playwright

    @staticmethod
    def parse_user_data(response: Dict) -> User:
        data_list = response.get("data")
        data = data_list[0]

        id = data["object_id"]
        first_name = NAME_REGEX.sub("", data.get("first_name", ""))
        last_name = NAME_REGEX.sub("", data.get("last_name", ""))
        phone = data.get("phone", "")
        email = data.get("email", "")

        return User(id, first_name, last_name, phone, email)

    @staticmethod
    def format_time(
        time: str, tz_name: str = "America/New_York"
    ) -> Optional[Dict[str, str]]:
        """
        Formats the given time string into a dictionary with date, dateTime, and timeZone keys.

        Args:
            time (str): The time string to be formatted.
            tz_name (str): Time zone name for localization. Defaults to "America/New_York".

        Returns:
            Optional[Dict[str, str]]: A dictionary containing the formatted date, dateTime, and timeZone information.
                                      Returns None if the time format is invalid.
        """
        try:
            dt = datetime.fromisoformat(time)
            tz = pytz.timezone(tz_name)
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            return {
                "date": dt.date().isoformat(),
                "dateTime": dt.isoformat(),
                "timeZone": tz_name,
            }
        except ValueError:
            logging.error("Invalid time format")
            return None
