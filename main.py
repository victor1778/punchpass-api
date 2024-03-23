from fastapi import FastAPI, Query
from typing import Annotated
from mangum import Mangum

from scraper import Scraper
from user_data_fetcher import fetch_punchpass_user_data, extract_user_data

app = FastAPI()
handler = Mangum(app)
scraper = Scraper()


@app.get("/")
async def read_schedule():
    schedule = scraper.get_schedule()
    return {"schedule": schedule}

@app.post("/user/")
async def read_user_email(email: str = Query(..., description="The email linked with Punchpass user account")):
    response = fetch_punchpass_user_data(email, scraper.cookies_store)
    data = extract_user_data(response)
    return data
