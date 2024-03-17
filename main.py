from fastapi import FastAPI
from mangum import Mangum

import cProfile
import pstats

from scraper import Scraper

app = FastAPI()
handler = Mangum(app)
scraper = Scraper()


@app.get("/")
async def read_schedule():
    schedule = scraper.get_schedule()
    return {"schedule": schedule}
