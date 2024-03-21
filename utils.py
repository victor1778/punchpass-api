import logging
import re
import sqlite3
from datetime import datetime
from typing import Dict, Literal, Optional

import pytz

from models import Event, User

NY_TZ = pytz.timezone("America/New_York")
NAME_REGEX = re.compile(r"<[^>]+>")


class Utils:
    @staticmethod
    def fetch_events_for_today() -> list[dict] | None:
        """Fetches schedule items from the database that have the start date or end date as today."""
        today_date = datetime.now().strftime("%Y-%m-%d")
        logging.info(f"Fetching today's events from the database")

        with sqlite3.connect("./database/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM Event 
                    WHERE date(StartDate) = ?
                    AND Title NOT LIKE "Sensual Move%"
                    AND Title NOT LIKE "Private Session%"
                    ORDER BY StartDateTime ASC
                    """
            cur.execute(query, (today_date,))
            items = cur.fetchall()

        if not items:
            return None

        schedule = []
        for item in items:
            event = Event(
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
                {"date": item[6], "dateTime": item[7], "timeZone": item[8]},
                {"date": item[9], "dateTime": item[10], "timeZone": item[11]},
                item[12],
            )
            schedule.append(event.to_dict())
        return schedule

    @staticmethod
    def fetch_schedule_item_by_id(
        item_id, type: Optional[Literal[1]] = None
    ) -> dict | Event | None:
        """Fetches a single schedule item from the database matching the given ID."""
        logging.info(f"Fetching event from the database with ID: {item_id}")

        with sqlite3.connect("./database/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM Event 
                    WHERE EventID = ?
                    """
            cur.execute(query, (item_id,))
            item = cur.fetchone()

            if item:
                event = Event(
                    id=item[0],
                    status=item[1],
                    url=item[2],
                    title=item[3],
                    location=item[4],
                    instructor=item[5],
                    start={"date": item[6], "dateTime": item[7], "timeZone": item[8]},
                    end={"date": item[9], "dateTime": item[10], "timeZone": item[11]},
                    timestamp=item[12],
                )
                if type is None:
                    return event.to_dict()
                else:
                    return event
            else:
                return None

    def fetch_user_by_email(email: str) -> dict | None:
        """Fetches a single user from the database matching the given email."""
        logging.info(f"Fetching user from the database with email: {email}")

        with sqlite3.connect("./database/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM User 
                    WHERE Email = ?
                    """
            cur.execute(query, (email,))
            item = cur.fetchone()

            if item:
                user = User(
                    id=item[0],
                    first_name=item[1],
                    last_name=item[2],
                    phone=item[3],
                    email=item[4],
                )
                return user.to_dict()
            else:
                return None

    @staticmethod
    def load_user(user: User) -> None:
        """Inserts a single User into the database."""
        logging.info(f"Loading User {user.id} to database")
        with sqlite3.connect("./database/database.db") as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO User
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user.id, user.first_name, user.last_name, user.phone, user.email),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                logging.error(
                    "Duplicate entry found. Skipping insertion for duplicate."
                )
            except Exception as e:
                logging.error(f"Error during insertion: {e}")

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
    def parse_user_data(response: Dict) -> User | None:
        data_list = response.get("data")
        if not data_list:
            return None

        data = data_list[0]
        id = data["object_id"]
        first_name = NAME_REGEX.sub("", data.get("first_name", ""))
        last_name = NAME_REGEX.sub("", data.get("last_name", ""))
        phone = data.get("phone", "")
        email = data.get("email", "")

        return User(int(id), first_name, last_name, phone, email)

    @staticmethod
    def format_time(
        time: str, tz_name: str = "America/New_York"
    ) -> Optional[Dict[str, str]]:
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
