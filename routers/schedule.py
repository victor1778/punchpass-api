import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Request

from dependencies import Utils

router = APIRouter(prefix="/schedule")
tasks = {}


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
    name = payload.get("name")

    if not name:
        return {"detail": "Name is required."}

    event = Utils.fetch_schedule_item_by_id(event_id, 1)
    if not event:
        raise HTTPException(
            status_code=404,
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
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )


@router.post("/check_in/bulk", status_code=202)
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
            "locations": ", ".join(task_urls),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check in {name}. Error: {str(e)}",
        )


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
