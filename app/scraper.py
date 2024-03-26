import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser

from dependencies import Utils
from models import CheckIn, Event, User

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

INSTRUCTOR_REGEX = re.compile(r"with\s+(.+?)(?:\s*⋅\s*(.+))?$")
END_ELEM_REGEX = re.compile(r"(.+)\s@\s\d+:\d+-(\d+:\d+\s[ap]m)")
START_ELEM_REGEX = re.compile(r"(.+)\s@\s(\d+:\d+)-\d+:\d+\s([ap]m)")


SBR_WS_CDP = "wss://brd-customer-hl_2b2127e4-zone-scraping_browser1-country-us:w5hhlx7pc45s@brd.superproxy.io:9222"


class Scraper:
    _instance: Optional["Scraper"] = None
    cookies_store: Dict[str, str] = {}

    def __new__(cls) -> "Scraper":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logging.info("Scraper instance created")
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "session"):
            self.client = httpx.Client()
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
        r = self.get_page(f"{self.baseurl}/account/sign_in")
        if r and r.status_code == 200:
            html = HTMLParser(r.text)
            auth_token = html.css_first("form.simple_form.account input").attributes[
                "value"
            ]
            logging.info("Authentication token retrieved")
            return auth_token
        logging.error("Failed to get authentication token")
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

    def _login(self) -> None:
        if not Scraper.cookies_store:
            auth_token = self._get_auth_token()
            email = os.environ.get("EMAIL")
            password = os.environ.get("PASSWORD")

            payload = {
                "authenticity_token": auth_token,
                "account[email]": email,
                "account[password]": password,
            }

            self.client.post(f"{self.baseurl}/account/sign_in", data=payload)
            self.get_page(
                f"{self.baseurl}/account/companies/12433/switch_to_admin_view"
            )

            self.cookies_store = {
                "force_login_key": self.client.cookies.get("force_login_key"),
                "remember_account_token": self.client.cookies.get(
                    "remember_account_token"
                ),
                "_punchpass52_session": self.client.cookies.get("_punchpass52_session"),
            }
            logging.info("Saved cookies to in-memory store")

    def get_page(self, url: str) -> Optional[httpx.Response]:
        try:
            response = self.client.get(url, headers=self.headers)
            return response
        except Exception as e:
            logging.error(f"Failed to fetch page: {url}. Error: {e}")
            return None

    def parse_schedule_item(self, elem: HTMLParser) -> Event:
        url = f"{self.baseurl}{elem.css_first('div.cell.auto.small-order-2.medium-auto.medium-order-2 strong a.with-icon').attrs['href']}"
        id = url.split("/")[-1]

        placeholder = elem.css_first(
            "div.cell.small-12.small-order-4.medium-shrink.medium-order-3 span"
        )
        if placeholder is None:
            status = "confirmed"
        else:
            if placeholder.attrs["class"] == "instance-status-icon cancelled":
                status = "cancelled"
            else:
                status = "confirmed"

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
        start = self._get_start_time(url)
        end = self._get_end_time(url)
        return Event(int(id), status, url, title, location, instructor, start, end)

    def _get_end_time(self, url: str) -> Optional[Dict[str, str]]:
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

    def _get_start_time(self, url: str) -> Optional[Dict[str, str]]:
        response = self.get_page(url)
        if response and response.status_code == 200:
            html = HTMLParser(response.text)
            start_elem = html.css_first("div.cell.auto h1 small").text().strip()
            start_elem_str = START_ELEM_REGEX.sub(r"\1 \2 \3", start_elem)
            try:
                dt = datetime.strptime(start_elem_str, "%B %d, %Y %I:%M %p")
                start = Utils.format_time(dt.isoformat())
                return start
            except ValueError:
                logging.error("Failed to parse end time.")
            return None

    def fetch_punchpass_user_data(self, email: str) -> User | None:
        url = f"https://app.punchpass.com/a/customers.json?columns[3][data]=email&columns[3][searchable]=true&columns[3][orderable]=true&columns[3][search][value]={email}&start=0&length=1"
        try:
            response = self.get_page(url)
            data = Utils.parse_user_data(response.json())
            if not data:
                return None
        except Exception as e:
            return {"detail": f"Could not fetch user from Punchpass. Error: {e}"}
        finally:
            return data

    async def user_check_in(self, user: User, event: Event, check_in: CheckIn) -> None:
        """
        Performs the check-in process for a user at an event.

        Args:
          user (User): The user object representing the user checking in.
          event (Event): The event object representing the event where the check-in is performed.
          check_in (CheckIn): The check-in object to be updated with the check-in status.

        Returns:
          None
        """
        start = time.perf_counter()
        name = f"{user.first_name} {user.last_name}"

        async with async_playwright() as p:
            if __debug__:
                browser = await p.chromium.connect_over_cdp(SBR_WS_CDP)
            else:
                browser = await p.chromium.launch()
            try:
                if __debug__:
                    logging.info(
                        f"Connected to Scraping Browser. Navigating to {event.url}..."
                    )
                else:
                    logging.info(f"Launching browser. Navigating to {event.url}...")

                context = await browser.new_context()
                await context.add_cookies(
                    Utils.format_cookies(self.cookies_store, self.baseurl)
                )
                page = await context.new_page()
                client = await page.context.new_cdp_session(page)

                if __debug__:
                    await client.send(
                        "Proxy.setLocation",
                        {"lat": 30.2712, "lon": -97.7417, "distance": 50},
                    )  # Set location to Austin, TX
                    await client.send(
                        "Captcha.setAutoSolve", {"autoSolve": False}
                    )  # Disable auto-solving captchas

                await client.send(
                    "Network.setCacheDisabled", {"cacheDisabled": False}
                )  # Force enable cache

                await page.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type
                        in ["image", "media", "font", "stylesheet"]
                        else route.continue_()
                    ),
                )
                await page.goto(f"{event.url}/attendances/new")
                customer_list = page.get_by_title("{{2*2}} lkslsk")
                await customer_list.wait_for(state="attached")
                input = page.get_by_placeholder("Search")
                await input.type(name)
                user_btn = page.get_by_title(name, exact=True)
                await user_btn.wait_for(state="attached")

                if not __debug__:
                    await user_btn.click()
            except Exception as e:
                check_in.status = "failed"
                check_in.updated_at = datetime.now(timezone.utc).isoformat()
                Utils.load_check_in(check_in)
                logging.error(f"Error checking in {name}: {e}")
            finally:
                check_in.status = "confirmed"
                check_in.updated_at = datetime.now(timezone.utc).isoformat()
                Utils.load_check_in(check_in)
                await browser.close()
                runtime = "{:.4f}".format(time.perf_counter() - start)
                logging.info(f"Request completed in {runtime} s")
