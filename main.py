from fastapi import FastAPI, Path
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

@app.post("/user/{email}")
async def read_schedule(email: Annotated[str, Path(title="The email of Punchpass user to get")]):
    response = fetch_punchpass_user_data(email, scraper.cookies_store)
    data = extract_user_data(response)
    return {"user": data}
