from fastapi import FastAPI
from mangum import Mangum

from scraper import Scraper

app = FastAPI()
handler = Mangum(app)
scraper = Scraper()


@app.get("/")
async def read_schedule():
    return {"schedule": scraper.get_schedule()}
