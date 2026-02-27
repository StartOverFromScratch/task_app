from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import captures, carryover, checklist, tasks

app = FastAPI(title="タスク管理システム", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 固定パス（/stale, /carryover-candidates）を /{task_id} より先に登録する
app.include_router(carryover.router, prefix="/tasks", tags=["carryover"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(checklist.router, prefix="/tasks", tags=["checklist"])
app.include_router(captures.router, prefix="/captures", tags=["captures"])


@app.get("/health")
def health():
    return {"status": "ok"}
