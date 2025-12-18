from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import engine, Base
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stock Trading API",
    description="Simulated stock trading API for algorithmic trading model training",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["Trading"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Stock Trading API",
        "version": "1.0.0",
        "description": "Simulated trading API for algorithmic trading",
        "endpoints": {
            "price": "/api/price",
            "trade": "/api/trade",
            "balance": "/api/balance",
            "holdings": "/api/holdings",
            "history": "/api/history",
            "market_status": "/api/market_status"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
