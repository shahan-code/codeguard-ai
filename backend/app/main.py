import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import auth_router, analysis_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codeguard")

app = FastAPI(
    title="CodeGuard AI",
    description="AI-assisted code quality & defect risk analysis API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened via reverse proxy / env config in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("CodeGuard AI backend started")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(analysis_router.router)
