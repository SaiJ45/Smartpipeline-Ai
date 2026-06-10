from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.loader import get_active_dataset
from database.connection import get_db
from database.models import PipelineRun
from ingestion.loader import DataLoader


router = APIRouter()


@router.post("")
def trigger_ingest():
    config = get_active_dataset()
    loader = DataLoader()
    loader.load_all(config)

    return {
        "status": "success",
        "message": "ETL pipeline triggered",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/status")
def ingest_status(db: Session = Depends(get_db)):
    runs = (
        db.query(PipelineRun)
        .order_by(PipelineRun.run_at.desc())
        .limit(5)
        .all()
    )

    return [
        {
            "id": run.id,
            "source_file": run.source_file,
            "records_in": run.records_in,
            "records_out": run.records_out,
            "status": run.status,
            "run_at": run.run_at,
        }
        for run in runs
    ]
