import logging
import sqlite3
import time

from selectolax.parser import HTMLParser

from models import Event
from scraper import Scraper

scraper = Scraper()

def extract_schedule() -> str:
    """Fetches and returns HTML content from the given URL."""
    logging.info(f"Fetching HTML content from {scraper.baseurl}/hub")
    response = scraper.get_page(f"{scraper.baseurl}/hub")
    html = response.text
    return html


def transform_schedule(html: str) -> list[Event]:
    """Parses HTML to extract and transform schedule information into Event objects."""
    logging.info("Parsing HTML to extract schedule items")
    content = HTMLParser(html)
    raw_schedule_items = content.css_first("div.instances-for-day").css("div.instance div.grid-x.grid-padding-x div.cell.auto div.instance__content"
    )
    date = content.css_first("div.instances-for-day").attrs["data-day"]
    return [
        scraper.parse_schedule_item(item, date) for item in raw_schedule_items
    ]


def load_schedule(cur, items: list[Event]) -> None:
    """Inserts multiple events into the database."""
    logging.info(f"Loading {len(items)} schedule items to database")
    values = []
    for item in items:
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
    except sqlite3.IntegrityError:
        logging.error("Duplicate entries found. Skipping insertion for duplicates.")
    except Exception as e:
        logging.error(f"Error during bulk insertion: {e}")


def main():
    start = time.time()
    html = extract_schedule()
    schedule = transform_schedule(html)

    with sqlite3.connect("../database.db") as conn:
        cur = conn.cursor()
        load_schedule(cur, schedule)
        conn.commit()
    end = time.time()
    runtime = '{:.4f}'.format(end - start)

    logging.info(f"Runtime: {runtime} s")


if __name__ == "__main__":
    main()