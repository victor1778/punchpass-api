import asyncio
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request

from dependencies import Utils
from models import CheckIn
from models.events import WriteUserToEvent, WriteUserToManyEvents

router = APIRouter(prefix="/schedule")


@router.get("/", response_model=dict[str, list[dict]], status_code=200)
async def read_schedule() -> dict[str, list[dict]]:
    schedule = Utils.fetch_events_for_today()

    if not schedule:
        raise HTTPException(status_code=404, detail="No events found for today.")

    return {"schedule": schedule}


@router.get("/{id}", response_model=dict[str, str], status_code=200)
async def read_event(
    id: Annotated[int, Path(title="The ID of the event to get")]
) -> dict:
    event = Utils.fetch_schedule_item_by_id(id)

    if not event:
        raise HTTPException(status_code=404, detail=f"Event {id} not found.")

    return event

@router.post("/{id}/check-in", status_code=202)
async def write_user_to_event(
    id: Annotated[int, Path(title="The ID of the event to get")],
    payload: WriteUserToEvent,
    request: Request,
) -> dict[str, str]:
    event_id = id
    first_name = payload.first_name
    last_name = payload.last_name

    if not first_name or not last_name:
        return HTTPException(
            status_code=400,
            detail="First and last name required for operation.",
        )

    user = Utils.fetch_user_by_name(first_name, last_name)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {first_name} {last_name} not found.",
        )

    event = Utils.fetch_schedule_item_by_id(event_id, 1)
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Could not check in {user.first_name} {user.last_name}. Schedule item {str(event_id)} not found.",
        )

    name = f"{user.first_name} {user.last_name}"

    check_in = CheckIn(
        id=str(uuid.uuid4()),
        event_id=event.id,
        user_id=user.id,
        status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    Utils.load_check_in(check_in)

    try:
        asyncio.create_task(
            request.app.state.scraper.user_check_in(user, event, check_in)
        )
        return {
            "detail": f"Check in request for {name} accepted",
            "id": check_in.id,
            "status": check_in.status,
            "location": f"{request.url.scheme}://18.220.119.66/schedule/check-in/status/{check_in.id}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {e}",
        )


@router.post("/check-in/bulk", status_code=202)
async def write_user_to_many_events(
    payload: WriteUserToManyEvents,
    request: Request,
) -> dict[str, str]:
    event_ids = payload.event_ids
    first_name = payload.first_name
    last_name = payload.last_name

    # Validate input
    if not event_ids or not first_name or not last_name:
        raise HTTPException(
            status_code=400,
            detail=f"Event IDs, first name, and last name required for operation.",
        )

    # Fetch user
    user = Utils.fetch_user_by_name(first_name, last_name)
    name = f"{first_name} {last_name}"
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {name} not found.",
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
    task_ids = []
    params = []
    for i in range(len(events)):
        check_in = CheckIn(
            id=str(uuid.uuid4()),
            event_id=events[i].id,
            user_id=user.id,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        Utils.load_check_in(check_in)
        task_ids.append(check_in.id)
        params.append((user, events[i], check_in))

    try:
        for param in params:
            asyncio.create_task(request.app.state.scraper.user_check_in(*param))

        event_ids = ", ".join(str(event.id) for event in events)
        task_urls = [
            f"{request.url.scheme}://18.220.119.66/schedule/check-in/status/{task_id}"
            for task_id in task_ids
        ]

        return {
            "detail": f"Check in request for {name} to {event_ids} accepted",
            "ids": ", ".join(task_ids),
            "locations": ", ".join(task_urls),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )


@router.get("/check-in/status/{id}", response_model=CheckIn, status_code=200)
async def get_check_in_status(
    id: Annotated[str, Path(title="The ID of the Check In to get")]
) -> dict[str, str]:
    check_in = Utils.fetch_check_in(id)

    if not check_in:
        raise HTTPException(status_code=204, detail=f"Task {id} not found")

    if check_in.status == "confirmed":
        raise HTTPException(status_code=200, detail=check_in.model_dump())
    elif check_in.status == "failed":
        raise HTTPException(status_code=500, detail=check_in.model_dump())
    else:
        raise HTTPException(status_code=302, detail=check_in.model_dump())
