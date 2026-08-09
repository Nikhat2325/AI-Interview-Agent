from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.interview import router


app = FastAPI(
    title="AI Interview Agent"
)


app.include_router(router)


BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


app.mount(
    "/frontend",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="frontend"
)


@app.get("/")
def home():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )