from fastapi import FastAPI

from routers import schedule, users
from scraper import Scraper

app = FastAPI(title="Punchpass API", openapi_url="/openapi.json")
app.state.scraper = Scraper()

app.include_router(users.router)
app.include_router(schedule.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
