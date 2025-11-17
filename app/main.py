import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_comps import router as comps_router
from app.api.routes_rentals import router as rentals_router
from app.api.routes_sales import router as sales_router
from app.api.routes_utils import router as utils_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Rental Buddy API",
    description="API for finding rental property comparables",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(rentals_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(comps_router, prefix="/api/v1")
app.include_router(utils_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Rental Buddy API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "dev" else False,
        log_level=settings.log_level.lower(),
    )
