import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Dataset


router = APIRouter()


def _dataset_to_dict(dataset: Dataset) -> dict:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "display_name": dataset.display_name,
        "source_type": dataset.source_type,
        "row_count": dataset.row_count,
        "created_at": dataset.created_at,
    }


def _rows_to_dicts(result):
    return [dict(row._mapping) for row in result]


@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [_dataset_to_dict(dataset) for dataset in datasets]


@router.get("/{name}")
def get_dataset(name: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.name == name).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return _dataset_to_dict(dataset)


@router.get("/{name}/preview")
def preview_dataset(name: str, db: Session = Depends(get_db)):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise HTTPException(status_code=400, detail="Invalid dataset name")

    result = db.execute(text(f"SELECT * FROM olist_{name} LIMIT 10"))
    return _rows_to_dicts(result)
