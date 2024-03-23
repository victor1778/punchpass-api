from fastapi import FastAPI

from routers import schedule, users
from scraper import Scraper

app = FastAPI(title="Punchpass API", openapi_url="/openapi.json")
app.state.scraper = Scraper()

<<<<<<< HEAD
app.include_router(schedule.router)
app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn

=======
app.include_router(users.router)
app.include_router(schedule.router)

if __name__ == "__main__":
    import uvicorn
>>>>>>> e58b33aa672f8dc0c0818c395dce657971d4cd55
    uvicorn.run("main:app", reload=True)
