from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import PipelineRun, SystemMetric


router = APIRouter()


@router.get("")
def metrics(db: Session = Depends(get_db)):
    grouped_metrics = {
        "api": [],
        "pipeline": [],
        "rag": [],
        "ml": [],
    }

    recent_metrics = (
        db.query(SystemMetric)
        .order_by(SystemMetric.recorded_at.desc())
        .limit(50)
        .all()
    )

    for metric in recent_metrics:
        metric_data = {
            "id": metric.id,
            "metric_name": metric.metric_name,
            "metric_value": metric.metric_value,
            "metric_metadata": metric.metric_metadata,
            "recorded_at": metric.recorded_at,
        }
        grouped_metrics.setdefault(metric.category, []).append(metric_data)

    return grouped_metrics


@router.get("/pipeline")
def pipeline_metrics(db: Session = Depends(get_db)):
    total_runs = db.query(func.count(PipelineRun.id)).scalar() or 0
    successful_runs = (
        db.query(func.count(PipelineRun.id))
        .filter(PipelineRun.status == "SUCCESS")
        .scalar()
        or 0
    )
    failed_runs = (
        db.query(func.count(PipelineRun.id))
        .filter(PipelineRun.status == "FAILED")
        .scalar()
        or 0
    )
    avg_throughput_rps = db.query(func.coalesce(func.avg(PipelineRun.throughput_rps), 0)).scalar()
    total_records_processed = db.query(func.coalesce(func.sum(PipelineRun.records_out), 0)).scalar()
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "success_rate": round(success_rate, 2),
        "avg_throughput_rps": float(avg_throughput_rps),
        "total_records_processed": int(total_records_processed),
    }
