import re

from fastapi import APIRouter, HTTPException, Request

from dependencies import Utils
from models.users import ReadUser, User

router = APIRouter(prefix="/users")

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


@router.post("/", response_model=User, status_code=200)
async def read_user(payload: ReadUser, request: Request) -> dict:
    email = payload.email
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
        return data.model_dump()

    return user
