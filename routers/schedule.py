import asyncio
import uuid
<<<<<<< HEAD
from datetime import datetime, timezone
=======
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Request

from dependencies import Utils
<<<<<<< HEAD
from models import CheckIn

router = APIRouter(prefix="/schedule")
=======

router = APIRouter(prefix="/schedule")
tasks = {}
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55


@router.get("/", status_code=200)
async def read_schedule() -> dict[str, list[dict]]:
    schedule = Utils.fetch_events_for_today()

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


@router.post("/{id}/check_in", status_code=202)
async def write_user_to_event(
    id: Annotated[int, Path(title="The ID of the event to get")],
    payload: Annotated[dict, Body(embed=True)],
    request: Request,
) -> dict[str, str]:
    event_id = id
<<<<<<< HEAD
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")

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
=======
    name = payload.get("name")

    if not name:
        return {"detail": "Name is required."}
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55

    event = Utils.fetch_schedule_item_by_id(event_id, 1)
    if not event:
        raise HTTPException(
            status_code=404,
<<<<<<< HEAD
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
            "location": f"{request.url.scheme}://{request.url.hostname}/check_in/status/{check_in.id}",
=======
            detail=f"Could not check in {name}. Schedule item {str(event_id)} not found.",
        )

    # Create a task and store it
    try:
        task = asyncio.create_task(
            request.app.state.scraper.user_check_in(name, event.url)
        )
        task_id = str(uuid.uuid4())
        tasks[task_id] = task
        return {
            "detail": f"Check-in request for {name} accepted",
            "task_id": task_id,
            "location": f"{request.url.scheme}://{request.url.hostname}/tasks/{task_id}",
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
<<<<<<< HEAD
            detail=f"Could not check in {name}. Error: {e}",
=======
            detail=f"Could not check in {name}. Error: {str(e)}",
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
        )


@router.post("/check_in/bulk", status_code=202)
<<<<<<< HEAD
async def write_user_to_many_events(
=======
async def write_user_to_event(
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
    payload: Annotated[dict, Body(embed=True)],
    request: Request,
) -> dict[str, str]:
    event_ids = payload.get("event_ids")
<<<<<<< HEAD
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")

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
=======
    name = payload.get("name")

    # Validate input
    if not event_ids or not name:
        raise HTTPException(
            status_code=400,
            detail=f"Event IDs and Name required for bulk operation.",
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
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
<<<<<<< HEAD
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
            f"{request.url.scheme}://{request.url.hostname}/check_in/status/{task_id}"
            for task_id in task_ids
        ]

        return {
            "detail": f"Check in request for {name} to {event_ids} accepted",
            "ids": ", ".join(task_ids),
=======
    params = [(name, event.url) for event in events]

    try:
        task_ids = []
        for param in params:
            task = asyncio.create_task(request.app.state.scraper.user_check_in(*param))
            task_id = str(uuid.uuid4())
            tasks[task_id] = task
            task_ids.append(task_id)

        host_url = f"{request.url.scheme}://{request.url.hostname}"
        event_ids = ", ".join(str(event.id) for event in events)
        task_urls = [f"{host_url}/tasks/{task_id}" for task_id in task_ids]
        

        return {
            "detail": f"Check-in request for {name} to {event_ids} accepted",
            "task_ids": ", ".join(task_ids),
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
            "locations": ", ".join(task_urls),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )


<<<<<<< HEAD
@router.get("/check_in/status/{id}")
async def get_check_in_status(
    id: Annotated[str, Path(title="The ID of the Check In to get")]
) -> dict[str, str]:
    check_in = Utils.fetch_check_in(id)
    if not check_in:
        raise HTTPException(status_code=204, detail=f"Task {id} not found")

    if check_in.status == "confirmed":
        raise HTTPException(status_code=200, detail=f"Task {id} completed succesfully")
    elif check_in.status == "failed":
        raise HTTPException(
            status_code=500, detail=f"Task {id} failed to check in user"
        )
    else:
        raise HTTPException(status_code=302, detail=f"Task {id} is still running")
=======
@router.get("/check_in/status/")
async def get_task_status(task_id: str) -> dict[str, str]:
    task = tasks.get(task_id)
    print(tasks)
    if not task:
        raise HTTPException(status_code=204, detail=f"Task {task_id} not found")

    if task.done():
        try:
            task.result()  # Re-raise any exceptions from the task
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error:{str(e)}")
        else:
            raise HTTPException(
                status_code=200, detail=f"Task {task_id} completed succesfully"
            )
    else:
        raise HTTPException(status_code=302, detail=f"Task {task_id} is still running")
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
