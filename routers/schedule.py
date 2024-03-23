import asyncio
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Request

from dependencies import Utils

router = APIRouter(prefix="/schedule")


@router.get("/", status_code=200)
async def read_schedule() -> dict[str, list[dict]]:
    schedule = await asyncio.to_thread(Utils.fetch_events_for_today)

    if not schedule:
        raise HTTPException(status_code=404, detail="No events found for today.")

    return {"schedule": schedule}


@router.get("/{id}", status_code=200)
async def read_event(
    id: Annotated[int, Path(title="The ID of the event to get")]
) -> dict:
    event = Utils.fetch_schedule_item_by_id(id)

    if not event:
        raise HTTPException(status_code=404, detail=f"Event {id} not found.")

    return event


@router.post("/{id}/check_in")
async def write_user_to_event(
    id: Annotated[int, Path(title="The ID of the event to get")],
    payload: Annotated[dict, Body(embed=True)],
    request: Request,
) -> dict[str, str]:
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
        await request.app.state.scraper.user_check_in(name, event.url)
        return {"detail": f"{name} checked in to {event.title}."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )


@router.post("/check_in/bulk")
async def write_user_to_event(
    payload: Annotated[dict, Body(embed=True)],
    request: Request,
) -> dict[str, str]:
    event_ids = payload.get("event_ids")
    name = payload.get("name")

    # Validate input
    if not event_ids or not name:
        raise HTTPException(
            status_code=400,
            detail=f"Event IDs and Name required for bulk operation.",
        )

    # Fetch events
    events = []
    for event_id in event_ids:
        event = Utils.fetch_schedule_item_by_id(event_id, 1)
        if not event:
            raise HTTPException(
                status_code=500,
                detail=f"Could not check in {name}. Error: Event {event_id} not found.",
            )
        events.append(event)

    # Prepare parameters for check-in
    params = [(name, event.url) for event in events]

    try:
        # Check-in user to events
        tasks = [request.app.state.scraper.user_check_in(*param) for param in params]
        await asyncio.gather(*tasks)
        return {
            "detail": f"{name} checked in to {', '.join(str(event.id) for event in events)}."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )
