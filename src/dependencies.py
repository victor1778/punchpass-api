import logging
import re
import sqlite3
from datetime import datetime
from typing import Literal, Optional

import pytz

from models import CheckIn, Event, User

NY_TZ = pytz.timezone("America/New_York")
NAME_REGEX = re.compile(r"<[^>]+>")


class Utils:
    @staticmethod
    def fetch_events_for_today() -> list[dict] | None:
        """Fetches schedule items from the database that have the start date or end date as today."""
        today = datetime.now(NY_TZ).date().isoformat()
        logging.info(f"today: {today}")
        logging.info(f"Fetching today's events from the database")
        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM event 
                    WHERE SUBSTR(DATE(start, 'localtime'), 1, 10) = ?
                    AND title NOT LIKE "Sensual Move%"
                    AND title NOT LIKE "Private Session%"
                    ORDER BY start ASC
                    """
            cur.execute(query, (today,))
            items = cur.fetchall()

        if not items:
            return None

        schedule = []
        for item in items:
            event = Event(
                id=item[0],
                status=item[1],
                url=item[2],
                created=item[3],
                updated=item[4],
                title=item[5],
                location=item[6],
                instructor=item[7],
                start=item[8],
                end=item[9],
            )
            schedule.append(event.model_dump())
        return schedule

    @staticmethod
    def fetch_schedule_item_by_id(
        item_id: int, type: Optional[Literal[1]] = None
    ) -> dict | Event | None:
        """Fetches a single schedule item from the database matching the given ID."""
        logging.info(f"Fetching event from the database with ID: {item_id}")

        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM event 
                    WHERE event_id = ?
                    """
            cur.execute(query, (item_id,))
            item = cur.fetchone()

            if item:
                event = Event(
                    id=item[0],
                    status=item[1],
                    url=item[2],
                    created=item[3],
                    updated=item[4],
                    title=item[5],
                    location=item[6],
                    instructor=item[7],
                    start=item[8],
                    end=item[9],
                )
                if type is None:
                    return event.model_dump()
                else:
                    return event

            return None

    @staticmethod
    def fetch_user_by_email(email: str) -> dict | None:
        """Fetches a single user from the database matching the given email."""
        logging.info(f"Fetching user from the database with email: {email}")

        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM user 
                    WHERE email = ?
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
                return user.model_dump()

            return None

    @staticmethod
    def fetch_user_by_name(first_name: str, last_name: str) -> User | None:
        """Fetches a single user from the database matching the given name."""
        logging.info(
            f"Fetching user from the database with name: {first_name} {last_name}"
        )

        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM user 
                    WHERE first_name = ?
                    AND last_name = ?
                    """
            cur.execute(query, (first_name, last_name))
            item = cur.fetchone()

            if item:
                user = User(
                    id=item[0],
                    first_name=item[1],
                    last_name=item[2],
                    phone=item[3],
                    email=item[4],
                )
                return user

            return None

    @staticmethod
    def fetch_check_in(id: str) -> CheckIn | None:
        """Fetches a single user from the database matching the given name."""
        logging.info(f"Fetching Check In from the database with id: {id}")

        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM check_in 
                    WHERE check_in_id = ?
                    """
            cur.execute(query, (id,))
            item = cur.fetchone()

            if item:
                check_in = CheckIn(
                    id=item[0],
                    event_id=item[1],
                    user_id=item[2],
                    status=item[3],
                    created=item[4],
                    updated=item[5],
                )
                return check_in

            return None

    @staticmethod
    def load_user(user: User) -> None:
        """Inserts a single User into the database."""
        logging.info(f"Loading User {user.id} to database")
        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO user
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
    def load_check_in(check_in: CheckIn) -> None:
        """Inserts a Check In receipt into the database."""
        logging.info(f"Loading Check In {check_in.id} to database")
        with sqlite3.connect("./src/db/database.db") as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO check_in
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(check_in_id) DO UPDATE SET
                        status=excluded.status,
                        updated=excluded.updated
                    """,
                    (
                        check_in.id,
                        check_in.event_id,
                        check_in.user_id,
                        check_in.status,
                        check_in.created,
                        check_in.updated,
                    ),
                )
                conn.commit()
            except Exception as e:
                logging.error(f"Error during insertion: {e}")

    @staticmethod
    def format_cookies(cookie_dict: dict, url: str) -> list[dict[str, str]]:
        cookies_for_playwright = []
        for name, value in cookie_dict.items():
            cookie = {
                "name": str(name),
                "value": str(value),
                "url": url,
            }
            cookies_for_playwright.append(cookie)

        return cookies_for_playwright

    @staticmethod
    def parse_user_data(response: dict) -> User | None:
        data_list = response.get("data")

        if not data_list:
            return None

        data = data_list[0]
        id = data["object_id"]
        first_name = NAME_REGEX.sub("", data.get("first_name", ""))
        last_name = NAME_REGEX.sub("", data.get("last_name", ""))
        phone = data.get("phone", "")
        email = data.get("email", "")

        return User(
            id=int(id),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
        )

    @staticmethod
    def format_time(dt: datetime) -> str | None:
        try:
            tz = pytz.timezone("America/New_York")
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            utc = dt.astimezone(pytz.utc)
            return utc.isoformat()
        except ValueError:
            logging.error("Invalid time format")
        return None
