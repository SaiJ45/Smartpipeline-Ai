from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.connection import get_db


router = APIRouter()


def _rows_to_dicts(result):
    return [dict(row._mapping) for row in result]


@router.get("/summary")
def data_summary(db: Session = Depends(get_db)):
    total_orders = db.execute(
        text("SELECT COUNT(*) as total_orders FROM olist_orders")
    ).scalar()
    total_revenue = db.execute(
        text("SELECT COALESCE(SUM(price), 0) as total_revenue FROM olist_order_items")
    ).scalar()
    avg_order_value = db.execute(
        text("SELECT COALESCE(AVG(price), 0) as avg_order_value FROM olist_order_items")
    ).scalar()
    total_customers = db.execute(
        text("SELECT COUNT(*) as total_customers FROM olist_customers")
    ).scalar()
    avg_review_score = db.execute(
        text("SELECT COALESCE(AVG(review_score), 0) as avg_review_score FROM olist_reviews")
    ).scalar()
    order_status = db.execute(
        text(
            """
            SELECT order_status, COUNT(*) as count
            FROM olist_orders
            GROUP BY order_status
            ORDER BY count DESC
            """
        )
    )

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "avg_order_value": float(avg_order_value),
        "total_customers": total_customers,
        "avg_review_score": float(avg_review_score),
        "order_status": _rows_to_dicts(order_status),
    }


@router.get("/top-products")
def top_products(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
            SELECT
                p.product_category_name,
                COUNT(*) as order_count
            FROM olist_order_items oi
            JOIN olist_products p ON oi.product_id = p.product_id
            GROUP BY p.product_category_name
            ORDER BY order_count DESC
            LIMIT 5
            """
        )
    )

    return _rows_to_dicts(result)


@router.get("/by-state")
def data_by_state(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
            SELECT
                c.customer_state,
                COUNT(*) as order_count,
                COALESCE(SUM(oi.price), 0) as total_revenue
            FROM olist_orders o
            JOIN olist_customers c ON o.customer_id = c.customer_id
            LEFT JOIN olist_order_items oi ON o.order_id = oi.order_id
            GROUP BY c.customer_state
            ORDER BY order_count DESC
            """
        )
    )

    return _rows_to_dicts(result)


@router.get("/anomalies")
def data_anomalies():
    return {
        "message": "ML anomalies will appear here after Day 4",
        "anomalies": [],
    }
