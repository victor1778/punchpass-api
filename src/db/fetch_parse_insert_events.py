import concurrent.futures
import logging
import os
import sqlite3
import sys
import time
from typing import List

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


def transform_schedule_item(item) -> Event:
    """Parses a single HTML item to extract and transform schedule information into an Event object."""
    return scraper.parse_schedule_item(item)


def transform_schedule(html: str) -> List[Event]:
    """Parses HTML to extract and transform schedule information into Event objects."""
    logging.info(f"Parsing HTML to extract schedule items")
    content = HTMLParser(html)
    raw_schedule_items = content.css(
        "div.instances-for-day div.instance div.grid-x.grid-padding-x div.cell.auto div.instance__content"
    )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        events = list(executor.map(transform_schedule_item, raw_schedule_items))

    return events


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
                item.created,
                item.updated,
                item.title,
                item.location,
                item.instructor,
                item.start,
                item.end,
            )
        )

    try:
        cur.executemany(
            """
            INSERT INTO event (event_id, status, url, created, updated, title, location, instructor, start, end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                status=excluded.status,
                location=excluded.location,
                instructor=excluded.instructor,
                start=excluded.start,
                end=excluded.end
            """,
            values,
        )
    except Exception as e:
        logging.error(f"Error during bulk insertion: {e}")


if __name__ == "__main__":
    start = time.perf_counter()
    html = extract_schedule()
    schedule = transform_schedule(html)

    with sqlite3.connect("./src/db/database.db") as conn:
        conn.isolation_level = None
        cur = conn.cursor()
        batch = [event for event in schedule]
        load_schedule(cur, batch)
        conn.commit()

    end = time.perf_counter()
    runtime = "{:.4f}".format(end - start)
    logging.info(f"Runtime: {runtime} s")
