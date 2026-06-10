import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routers.ask import router as ask_router
from api.routers.auth_router import router as auth_router
from api.routers.data import router as data_router
from api.routers.datasets import router as datasets_router
from api.routers.forecast import router as forecast_router
from api.routers.ingest import router as ingest_router
from api.routers.metrics import router as metrics_router
from database.connection import SessionLocal
from database.models import Dataset, SystemMetric


app = FastAPI(
    title="SmartPipeline AI",
    version="1.0.0",
    description="Intelligent data pipeline with AI-powered insights",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def record_request_latency(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start) * 1000

    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.name == "api").first()
        if dataset is None:
            dataset = Dataset(
                name="api",
                display_name="API Metrics",
                source_type="api",
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)

        db.add(
            SystemMetric(
                dataset_id=dataset.id,
                category="api",
                metric_name=request.url.path,
                metric_value=latency_ms,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return response


app.include_router(ingest_router, prefix="/ingest")
app.include_router(data_router, prefix="/data")
app.include_router(forecast_router, prefix="/forecast")
app.include_router(ask_router, prefix="/ask")
app.include_router(metrics_router, prefix="/metrics")
app.include_router(datasets_router, prefix="/datasets")
app.include_router(auth_router, prefix="/auth")


@app.get("/")
def root():
    return {
        "status": "ok",
        "timestamp": time.time(),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
