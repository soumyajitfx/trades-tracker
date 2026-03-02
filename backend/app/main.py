from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine, run_schema_migrations
from app.routers import auth, trades

app = FastAPI(title="MT5 Trade Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
run_schema_migrations()

app.include_router(auth.router)
app.include_router(trades.router)


@app.get("/health")
def health():
    return {"status": "ok"}
