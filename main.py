import asyncio
import sqlite3
from typing import Dict

from fastapi import FastAPI, HTTPException

from scraper import Scraper
from utils import Utils

app = FastAPI()
scraper = Scraper()


@app.get("/schedule")
async def read_schedule():
    schedule = Utils.fetch_events_for_today()
    return {"schedule": schedule}


@app.get("/schedule/{id}")
async def read_event(id: int):
    schedule_item = Utils.fetch_schedule_item_by_id(id)
    if schedule_item is None:
        raise HTTPException(status_code=404, detail=f"Schedule item {id} not found.")
    return schedule_item


@app.post("/schedule/{id}/check_in")
async def write_user_to_event(id: int, payload: Dict):
    event_id = id
    name = payload.get("name")

    if not name:
        return {"detail": "Name is required."}

    event = Utils.fetch_schedule_item_by_id(event_id, 1)
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Could not check in {name}. Schedule item {str(event_id)} not found.",
        )

    try:
        await scraper.user_check_in(name, event.url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )
    finally:
        return {"detail": f"{name} checked in to {event.title}."}


@app.post("/schedule/check_in/bulk")
async def write_user_to_event(payload: Dict):
    event_ids: list[int] = payload.get("event_ids")
    name: str = payload.get("name")

    # Validate input
    if not event_ids or not name:
        raise HTTPException(
            status_code=400,
            detail=f"Event IDs and Name required for bulk operation.",
        )

    if not event_ids:
        raise HTTPException(
            status_code=400,
            detail=f"At least one Event ID required for bulk operation.",
        )

    if not name:
        raise HTTPException(
            status_code=400,
            detail=f"Name requirer for bulk operation.",
        )

    # Fetch events
    events = []
    for event_id in event_ids:
        event = Utils.fetch_schedule_item_by_id(event_id, 1)
        if not event:
            raise HTTPException(
                status_code=500,
                detail=f"Could not check in {name}. Error: {str(e)}",
            )
        events.append(event)

    # Prepare parameters for check-in
    params = [(name, event.url) for event in events]

    try:
        # Check-in user to events
        tasks = [scraper.user_check_in(*param) for param in params]
        await asyncio.gather(*tasks)
        return {
            "detail": f"{name} checked in to {', '.join(str(event.id) for event in events)}."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )


@app.post("/user")
async def read_user(payload: Dict):
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail=f"Email required for operation.",
        )

    user = Utils.fetch_user_by_email(email)
    if user is None:
        data = scraper.fetch_punchpass_user_data(email)
        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with email {email} not found.",
            )
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            Utils.load_user(cur, data)
            conn.commit()
        return data.to_dict()
    else:
        return user
