from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, feedback, history, init

app = FastAPI(title="Zchat Mock API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(init.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(history.router)
