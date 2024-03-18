from typing import Dict

from fastapi import FastAPI, HTTPException

from scraper import Scraper
from utils import Utils

app = FastAPI()
scraper = Scraper()


@app.get("/schedule")
async def read_schedule():
    scraper.get_schedule()
    return {"schedule": scraper._get_schedule_store()}


@app.get("/schedule/{id}")
async def read_schedule_item(id: str):
    if not scraper._get_schedule_store():
        scraper.get_schedule()

    schedule_lookup = {item.id: item for item in scraper._get_schedule_store()}
    item = schedule_lookup.get(id)

    if item is not None:
        return item.to_dict()
    else:
        raise HTTPException(
            status_code=404, detail=f"Schedule item with ID {id} not found"
        )


@app.post("/users/fetch-data")
async def read_user_email(request_data: Dict):
    email = request_data.get("email")
    if not email:
        return {"error": "Email is required."}
    response = scraper.fetch_punchpass_user_data(email)
    data = Utils.parse_user_data(response)
    return data
