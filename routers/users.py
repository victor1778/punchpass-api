import re
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Request

from dependencies import Utils

router = APIRouter(prefix="/users")

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


@router.post("/", status_code=201)
<<<<<<< HEAD
async def read_user(
    payload: Annotated[dict, Body(embed=True)], request: Request
) -> dict:
=======
async def read_user(payload: Annotated[dict, Body(embed=True)], request: Request) -> dict:
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email required for operation.",
        )

    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format.",
        )

    user = Utils.fetch_user_by_email(email)
    if not user:
        data = request.app.state.scraper.fetch_punchpass_user_data(email)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"User with email {email} not found.",
            )
        Utils.load_user(data)
        return data.to_dict()

    return user
