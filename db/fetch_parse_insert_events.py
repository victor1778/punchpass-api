import logging
import os
import sqlite3
import sys
import time
from typing import Generator

from selectolax.parser import HTMLParser

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models import Event
from scraper import Scraper

scraper = Scraper()


def extract_schedule() -> str:
    """Fetches and returns HTML content from the given URL."""
    logging.info(f"Fetching HTML content from {scraper.baseurl}/hub")
    response = scraper.get_page(f"{scraper.baseurl}/hub")
    html = response.text
    return html


def transform_schedule(html: str) -> Generator[Event, None, None]:
    """Parses HTML to extract and transform schedule information into Event objects."""
    logging.info(f"Parsing HTML to extract schedule items")
    content = HTMLParser(html)
    raw_schedule_items = content.css_first("div.instances-for-day").css(
        "div.instance div.grid-x.grid-padding-x div.cell.auto div.instance__content"
    )
    date = content.css_first("div.instances-for-day").attrs["data-day"]

    for item in raw_schedule_items:
        yield scraper.parse_schedule_item(item, date)


def load_schedule(cur: sqlite3.Cursor, batch: list[Event]) -> None:
    """Inserts multiple events into the database."""
    logging.info(f"Loading {len(batch)} schedule items to database")
    values = []
    for item in batch:
        values.append(
            (
                item.id,
                item.status,
                item.url,
                item.title,
                item.location,
                item.instructor,
                item.start["date"],
                item.start["dateTime"],
                item.start["timeZone"],
                item.end["date"],
                item.end["dateTime"],
                item.end["timeZone"],
                item.timestamp,
            )
        )

    try:
        cur.executemany(
            """
            INSERT INTO Event 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(EventID) DO UPDATE SET
                Status=excluded.Status,
                Location=excluded.Location,
                Instructor=excluded.Instructor,
                StartDate=excluded.StartDate,
                StartDateTime=excluded.StartDateTime,
                EndDate=excluded.EndDate,
                EndDateTime=excluded.EndDateTime
            WHERE EventID=excluded.EventID;
            """,
            values,
        )
    except Exception as e:
        logging.error(f"Error during bulk insertion: {e}")


if __name__ == "__main__":
    start = time.perf_counter()
    html = extract_schedule()
    schedule = transform_schedule(html)

    with sqlite3.connect("./db/database.db") as conn:
        cur = conn.cursor()
        batch = [event for event in schedule]
        load_schedule(cur, batch)
        conn.commit()

    end = time.perf_counter()
    runtime = "{:.4f}".format(end - start)
    logging.info(f"Runtime: {runtime} s")
