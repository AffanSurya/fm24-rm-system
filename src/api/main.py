from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.api.state import app_state
from src.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data and fit PCA on startup
    print("Starting up... Loading data and fitting PCA.")
    app_state.load_data()
    yield
    print("Shutting down.")

app = FastAPI(
    title="FM24 Recommendation Engine",
    description="A multi-objective optimization and recommendation engine for Football Manager 24",
    version="1.0.0",
    lifespan=lifespan
)

# In a real setup, configure CORS here
app.include_router(router)
