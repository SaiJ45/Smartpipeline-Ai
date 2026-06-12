import pandas as pd
from sqlalchemy import text

from database.connection import SessionLocal


class DataChunker:
    """Build text chunks from joined Olist order data for RAG indexing."""

    def build_chunks(self, sample_size=50000) -> list:
        query = text(
    """
    SELECT
        o.order_id,
        o.order_status,
        DATE(o.order_purchase_timestamp) as purchase_date,
        o.delivery_delay_days,
        c.customer_city,
        c.customer_state,
        COALESCE(ct.product_category_name_english, p.product_category_name, 'unknown') as product_category_name_english,
        oi.price,
        oi.freight_value,
        r.review_score,
        r.review_comment_message
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    JOIN olist_order_items oi ON o.order_id = oi.order_id
    LEFT JOIN olist_products p ON oi.product_id = p.product_id
    LEFT JOIN olist_category_translation ct ON p.product_category_name = ct.product_category_name
    LEFT JOIN olist_reviews r ON o.order_id = r.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    LIMIT :sample_size
    """
)

        db = SessionLocal()
        try:
            result = db.execute(query, {"sample_size": sample_size})
            df = pd.DataFrame(result.mappings().all())
        finally:
            db.close()

        chunks = []
        for _, row in df.iterrows():
            chunks.append(
                {
                    "order_id": self._format_value(row.get("order_id")),
                    "text": self._render_chunk(row),
                    "metadata": {
                        "date": self._format_value(row.get("purchase_date")),
                        "state": self._format_value(row.get("customer_state")),
                        "category": self._format_value(row.get("product_category_name_english")),
                        "review_score": self._format_value(row.get("review_score")),
                    },
                }
            )

        return chunks

    def _render_chunk(self, row) -> str:
        comment = self._format_value(row.get("review_comment_message"))
        if comment != "N/A" and len(comment) > 200:
            comment = comment[:200]

        return (
            f"Order {self._format_value(row.get('order_id'))} "
            f"placed on {self._format_value(row.get('purchase_date'))} "
            f"by customer from {self._format_value(row.get('customer_city'))}, "
            f"{self._format_value(row.get('customer_state'))}. "
            f"Status: {self._format_value(row.get('order_status'))}. "
            f"Category: {self._format_value(row.get('product_category_name_english'))}. "
            f"Price: R${self._format_money(row.get('price'))}. "
            f"Delivery delay: {self._format_value(row.get('delivery_delay_days'))} days. "
            f"Review score: {self._format_value(row.get('review_score'))}/5. "
            f"Comment: {comment}"
        )

    def _format_value(self, value) -> str:
        if pd.isna(value):
            return "N/A"

        return str(value)

    def _format_money(self, value) -> str:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):.2f}"
