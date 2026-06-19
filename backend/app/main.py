from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat, facilities, insights, reports

app = FastAPI(title="Medelite Facility Assessment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(facilities.router)
app.include_router(reports.router)
app.include_router(insights.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
