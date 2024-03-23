import logging
import re
import sqlite3
from datetime import datetime
from typing import Literal, Optional

import pytz

<<<<<<< HEAD
from models import CheckIn, Event, User
=======
from models import Event, User
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55

NY_TZ = pytz.timezone("America/New_York")
NAME_REGEX = re.compile(r"<[^>]+>")


class Utils:
    @staticmethod
    def fetch_events_for_today() -> list[dict] | None:
        """Fetches schedule items from the database that have the start date or end date as today."""
        today = datetime.now().strftime("%Y-%m-%d")
        logging.info(f"Fetching today's events from the database")
        with sqlite3.connect("./db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM Event 
                    WHERE date(StartDate) = ?
                    AND Title NOT LIKE "Sensual Move%"
                    AND Title NOT LIKE "Private Session%"
                    ORDER BY StartDateTime ASC
                    """
            cur.execute(query, (today,))
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
        item_id: int, type: Optional[Literal[1]] = None
    ) -> dict | Event | None:
        """Fetches a single schedule item from the database matching the given ID."""
        logging.info(f"Fetching event from the database with ID: {item_id}")

        with sqlite3.connect("./db/database.db") as conn:
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
<<<<<<< HEAD

            return None

    @staticmethod
=======
            
            return None

>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
    def fetch_user_by_email(email: str) -> dict | None:
        """Fetches a single user from the database matching the given email."""
        logging.info(f"Fetching user from the database with email: {email}")

        with sqlite3.connect("./db/database.db") as conn:
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
<<<<<<< HEAD

            return None

    @staticmethod
    def fetch_user_by_name(first_name: str, last_name: str) -> User | None:
        """Fetches a single user from the database matching the given name."""
        logging.info(
            f"Fetching user from the database with name: {first_name} {last_name}"
        )

        with sqlite3.connect("./db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM User 
                    WHERE FirstName = ?
                    AND LastName = ?
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

        with sqlite3.connect("./db/database.db") as conn:
            cur = conn.cursor()
            query = """
                    SELECT * FROM CheckIn 
                    WHERE CheckInId = ?
                    """
            cur.execute(query, (id,))
            item = cur.fetchone()

            if item:
                check_in = CheckIn(
                    id=item[0],
                    event_id=item[1],
                    user_id=item[2],
                    status=item[3],
                    created_at=item[4],
                    updated_at=item[5],
                )
                return check_in

=======
            
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
            return None

    @staticmethod
    def load_user(user: User) -> None:
        """Inserts a single User into the database."""
        logging.info(f"Loading User {user.id} to database")
        with sqlite3.connect("./db/database.db") as conn:
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
<<<<<<< HEAD
    def load_check_in(check_in: CheckIn) -> None:
        """Inserts a Check In receipt into the database."""
        logging.info(f"Loading Check In {check_in.id} to database")
        with sqlite3.connect("./db/database.db") as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO CheckIn
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(CheckInID) DO UPDATE SET
                        Status=excluded.Status,
                        UpdatedAt=excluded.UpdatedAt
                    """,
                    (
                        check_in.id,
                        check_in.event_id,
                        check_in.user_id,
                        check_in.status,
                        check_in.created_at,
                        check_in.updated_at,
                    ),
                )
                conn.commit()
            except Exception as e:
                logging.error(f"Error during insertion: {e}")

    @staticmethod
=======
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
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

        return User(int(id), first_name, last_name, phone, email)

    @staticmethod
    def format_time(
        time: str, tz_name: str = "America/New_York"
<<<<<<< HEAD
    ) -> dict[str, str] | None:
=======
    ) -> dict[str, str] | None :
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
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
<<<<<<< HEAD

=======
        
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
        return None
