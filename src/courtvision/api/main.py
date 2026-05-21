"""CourtVision AI - FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from courtvision.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CourtVision AI",
    description="AI-Powered NBA Prediction Market on Polygon via Azuro Protocol",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("CourtVision AI starting up...")
    logger.info("Chain: Polygon Amoy (80002)")
    logger.info("Protocol: Azuro Protocol")
    logger.info("AI Engine: Qwen LLM (DashScope)")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "courtvision.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
