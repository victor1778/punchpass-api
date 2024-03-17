import logging
import re
from datetime import datetime

import pytz
import requests
from selectolax.parser import HTMLParser

import creds
from models import ScheduleItem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def format_time(time) -> dict[str, str]:
    logging.info("Running format_start() function")
    dt = datetime.fromisoformat(time)
    nyc_tz = pytz.timezone("America/New_York")
    dt = dt.astimezone(nyc_tz)
    return {
        "date": dt.date().isoformat(),
        "dateTime": dt.isoformat(),
        "timeZone": "America/New_York",
    }


class Scraper:
    def __init__(self) -> None:
        logging.info("Creating Scraper instance")
        self.session = requests.session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.baseurl = "https://app.punchpass.com"
        self._login()

    def _get_auth_token(self) -> str:
        logging.info("Running _get_auth_token() function")

        r = self.get_page(self.baseurl + "/account/sign_in")
        if r.status_code == 200:
            html = HTMLParser(r.text)
            auth_token = html.css_first("form.simple_form.account input").attributes[
                "value"
            ]
            return auth_token
        else:
            logging.error("Failed to get authentication token.")

        return ""

    def _login(self) -> None:
        logging.info("Running _login() function")
        auth_token = self._get_auth_token()

        payload = {
            "authenticity_token": auth_token,
            "account[email]": creds.email,
            "account[password]": creds.password,
        }

        self.session.post(self.baseurl + "/account/sign_in", data=payload)
        self.get_page(self.baseurl + "/account/companies/12433/switch_to_admin_view")

    def get_page(self, url) -> requests.Response:
        logging.info("Running get_page(params) function")
        response = self.session.get(url, headers=self.headers)
        return response

    def get_schedule(self) -> list[ScheduleItem]:
        logging.info("Running get_schedule() function")
        r = self.get_page(self.baseurl + "/hub")
        if r.status_code == 200:
            return self.get_schedule_items(r.text)
        raise Exception("Failed to retrieve schedule data")

    def parse_schedule_item(self, elem, date) -> ScheduleItem:
        logging.info("Running parse_schedule_item() function")

        url = (
            self.baseurl
            + elem.css_first(
                "div.cell.auto.small-order-2.medium-auto.medium-order-2 strong a.with-icon"
            ).attrs["href"]
        )

        id = url.split("/")[-1]

        status = (
            "cancelled"
            if (
                elem.css_first(
                    "cell small-12 small-order-4 medium-shrink medium-order-3 span.instance-status-icon.cancelled"
                )
            )
            else "confirmed"
        )

        title = (
            elem.css_first(
                "div.cell.auto.small-order-2.medium-auto.medium-order-2 strong a.with-icon"
            )
            .text()
            .strip()
        )

        instructor_elem = (
            elem.css_first(
                "div.cell.auto.small-order-2.medium-auto.medium-order-2 span.instance-instructor"
            )
            .text()
            .strip()
        )
        match = re.search(r"with (.*?)(?:\s*⋅\s*(.*))?$", instructor_elem)
        instructor = match.group(1)
        location = match.group(2) if match.group(2) else ""

        start_elem = (
            elem.css_first(
                "div.cell.small-12.small-order-1.medium-2.medium-order-1.large-2"
            )
            .text()
            .strip()
        )
        dt = datetime.strptime(f"{date} {start_elem}", "%B %d, %Y %I:%M %p")
        start = dt.isoformat()
        end = self.get_end_time(url)

        return ScheduleItem(
            id,
            status,
            url,
            title,
            location,
            instructor,
            format_time(start),
            format_time(end),
        )

    def get_schedule_items(self, html_content) -> list[ScheduleItem]:
        logging.info("Running get_schedule_items() function")

        html = HTMLParser(html_content)
        elems = html.css_first("div.instances-for-day").css(
            "div.instance div.grid-x.grid-padding-x div.cell.auto div.instance__content"
        )
        elems_date = html.css_first("div.instances-for-day").attrs["data-day"]
        return [self.parse_schedule_item(elem, elems_date) for elem in elems]

    def get_end_time(self, url) -> str:
        r = self.get_page(url)
        if r.status_code == 200:
            html = HTMLParser(r.text)
            end_elem = html.css_first("div.cell.auto h1 small").text().strip()
            end_elem_str = re.sub(r"(.*) @ \d+:\d+-(\d+:\d+ [ap]m)", r"\1 \2", end_elem)
            dt = datetime.strptime(end_elem_str, "%B %d, %Y %I:%M %p")
            end = dt.isoformat()
            return end
        return ""
