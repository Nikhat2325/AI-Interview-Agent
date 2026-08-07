from fastapi import FastAPI
from app.interview import router

app = FastAPI(
    title="AI Interview Agent"
)


app.include_router(router)


@app.get("/")
def home():
    return {
        "message":"AI Interview Agent Running"
    }