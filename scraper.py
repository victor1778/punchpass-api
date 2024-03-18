import logging
import re
from datetime import datetime
from functools import lru_cache
from typing import Dict, Optional

import requests
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser

import creds
from models import ScheduleItem
from utils import CachedList, Utils

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

INSTRUCTOR_REGEX = re.compile(r"with\s+(.+?)(?:\s*⋅\s*(.+))?$")
END_ELEM_REGEX = re.compile(r"(.+)\s@\s\d+:\d+-(\d+:\d+\s[ap]m)")
SBR_WS_CDP = "wss://brd-customer-hl_2b2127e4-zone-scraping_browser1-country-us:w5hhlx7pc45s@brd.superproxy.io:9222"


class Scraper:
    _instance: Optional["Scraper"] = None
    cookies_store: Dict[str, str] = {}

    def __new__(cls) -> "Scraper":
        logging.info("Creating Scraper instance")
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logging.info("Scraper instance created")
        return cls._instance

    def __init__(self) -> None:
        logging.info("Initializing Scraper")
        if not hasattr(self, "session"):
            self.session = requests.session()
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            self.baseurl = "https://app.punchpass.com"
            self._login()

    def _get_auth_token(self) -> str:
        """
        Retrieves the authentication token from the login page.

        Returns:
            str: The authentication token.
        """
        logging.info("Getting authentication token.")
        r = self.get_page(f"{self.baseurl}/account/sign_in")
        if r and r.status_code == 200:
            html = HTMLParser(r.text)
            auth_token = html.css_first("form.simple_form.account input").attributes[
                "value"
            ]
            logging.info("Authentication token retrieved.")
            return auth_token
        logging.error("Failed to get authentication token.")
        return ""

    def _load_cookies(self) -> None:
        """
        Loads cookies from the in-memory store.
        """
        logging.info("Loading cookies.")
        if Scraper.cookies_store:
            try:
                self.session.cookies.update(Scraper.cookies_store)
                logging.info("Loaded cookies from in-memory store")
            except Exception as e:
                logging.error(f"Failed to load cookies: {e}")

    def _save_cookies_to_store(self) -> None:
        """
        Saves cookies to the in-memory store.
        """
        try:
            Scraper.cookies_store = self.session.cookies.get_dict()
            logging.info("Saved cookies to in-memory store")
        except Exception as e:
            logging.error(f"Failed to save cookies: {e}")

    def _login(self) -> None:
        """
        Performs the login process.
        """
        if not Scraper.cookies_store:
            auth_token = self._get_auth_token()

            payload = {
                "authenticity_token": auth_token,
                "account[email]": creds.email,
                "account[password]": creds.password,
            }
            self.session.post(f"{self.baseurl}/account/sign_in", data=payload)
            self.get_page(
                f"{self.baseurl}/account/companies/12433/switch_to_admin_view"
            )
            self._save_cookies_to_store()

    def get_page(self, url: str) -> Optional[requests.Response]:
        """
        Fetches a page from the given URL.

        Args:
            url (str): The URL of the page to fetch.

        Returns:
            requests.Response: The response object if successful, None otherwise.
        """
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"Failed to fetch page: {url}. Error: {e}")
            return None

    @lru_cache(maxsize=128)
    def _get_schedule_store(self) -> list[ScheduleItem]:
        return CachedList()

    def get_schedule(self) -> list[ScheduleItem]:
        """
        Retrieves the schedule data.

        Returns:
            list[ScheduleItem]: A list of ScheduleItem objects representing the schedule.

        Raises:
            Exception: If failed to retrieve schedule data.
        """
        r = self.get_page(f"{self.baseurl}/hub")
        if r and r.status_code == 200:
            schedule_items = self.get_schedule_items(r.text)
            self._get_schedule_store().extend(schedule_items)
            return self._get_schedule_store()
        raise Exception("Failed to retrieve schedule data")

    def parse_schedule_item(self, elem: HTMLParser, date: str) -> ScheduleItem:
        """
        Parses a schedule item from the given HTML element and date.

        Args:
            elem (HTMLParser): The HTML element representing the schedule item.
            date (str): The date of the schedule item.

        Returns:
            ScheduleItem: The parsed ScheduleItem object.
        """
        url = f"{self.baseurl}{elem.css_first('div.cell.auto.small-order-2.medium-auto.medium-order-2 strong a.with-icon').attrs['href']}"
        item_id = url.split("/")[-1]
        status = (
            "cancelled"
            if elem.css_first(
                "cell small-12 small-order-4 medium-shrink medium-order-3 span.instance-status-icon.cancelled"
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
        match = INSTRUCTOR_REGEX.search(instructor_elem)
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
        start = Utils.format_time(dt.isoformat())
        end = self.get_end_time(url)
        return ScheduleItem(
            item_id, status, url, title, location, instructor, start, end
        )

    def get_schedule_items(self, html_content: str) -> list[ScheduleItem]:
        """
        Parses and returns a list of ScheduleItem objects from the given HTML content.

        Args:
            html_content (str): The HTML content containing the schedule data.

        Returns:
            list[ScheduleItem]: A list of ScheduleItem objects representing the schedule.
        """
        html = HTMLParser(html_content)
        elems = html.css_first("div.instances-for-day").css(
            "div.instance div.grid-x.grid-padding-x div.cell.auto div.instance__content"
        )
        elems_date = html.css_first("div.instances-for-day").attrs["data-day"]
        return [self.parse_schedule_item(elem, elems_date) for elem in elems]

    def get_end_time(self, url: str) -> Optional[Dict[str, str]]:
        """
        Retrieves the end time for the given URL.

        Args:
            url (str): The URL of the schedule item.

        Returns:
            Dict[str, str]: A dictionary containing the formatted end time information,
                            or None if the end time could not be parsed.
        """
        response = self.get_page(url)
        if response and response.status_code == 200:
            html = HTMLParser(response.text)
            end_elem = html.css_first("div.cell.auto h1 small").text().strip()
            end_elem_str = END_ELEM_REGEX.sub(r"\1 \2", end_elem)
            try:
                dt = datetime.strptime(end_elem_str, "%B %d, %Y %I:%M %p")
                end = Utils.format_time(dt.isoformat())
                return end
            except ValueError:
                logging.error("Failed to parse end time.")
        return None

    def fetch_punchpass_user_data(self, email: str) -> Dict:
        url = f"https://app.punchpass.com/a/customers.json?columns[3][data]=email&columns[3][searchable]=true&columns[3][orderable]=true&columns[3][search][value]={email}&start=0&length=1"
        try:
            response = self.get_page(url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        return data

    async def user_check_in(self, name: str, url: str):
        async with async_playwright() as p:
            logging.info(f"Connecting to Scraping Browser...")
            browser = await p.chromium.connect_over_cdp(SBR_WS_CDP)
            try:
                logging.info(f"Connected! Navigating...")
                context = await browser.new_context()
                page = await context.new_page()
                await context.add_cookies(
                    Utils.load_cookies(self.cookies_store, self.baseurl)
                )
                await page.goto(f"{url}/attendances/new")
                input = page.get_by_placeholder("Search")
                await input.type(name)
                user_btn = page.get_by_title(name, exact=True)
                await user_btn.click()
                logging.info(f"Successfully checked in {name}")
            except Exception as e:
                logging.error(f"Error checking in {name}: {e}")
            finally:
                await browser.close()
