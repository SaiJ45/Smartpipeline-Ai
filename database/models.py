from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    Float,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from database.connection import engine

# Create base class for declarative models
Base = declarative_base()


class Dataset(Base):
    """Dataset metadata and statistics."""
    
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    source_type = Column(String(50), nullable=True)
    row_count = Column(BigInteger, nullable=True)
    column_count = Column(Integer, nullable=True)
    schema_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_loaded_at = Column(DateTime, nullable=True)
    
    # Relationships
    pipeline_runs = relationship("PipelineRun", back_populates="dataset", cascade="all, delete-orphan")
    system_metrics = relationship("SystemMetric", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return (
            f"<Dataset(id={self.id}, name='{self.name}', display_name='{self.display_name}', "
            f"row_count={self.row_count}, column_count={self.column_count}, "
            f"created_at={self.created_at})>"
        )


class PipelineRun(Base):
    """Pipeline execution records."""
    
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    source_file = Column(String(500), nullable=True)
    records_in = Column(BigInteger, nullable=True)
    records_out = Column(BigInteger, nullable=True)
    records_rejected = Column(BigInteger, nullable=True)
    rejection_rate = Column(Float, nullable=True)
    duration_secs = Column(Float, nullable=True)
    throughput_rps = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    run_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="pipeline_runs")
    
    def __repr__(self) -> str:
        return (
            f"<PipelineRun(id={self.id}, dataset_id={self.dataset_id}, "
            f"records_in={self.records_in}, records_out={self.records_out}, "
            f"status='{self.status}', run_at={self.run_at})>"
        )


class SystemMetric(Base):
    """System performance metrics."""
    
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    category = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_metadata = Column(JSON, nullable=True)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="system_metrics")
    
    def __repr__(self) -> str:
        return (
            f"<SystemMetric(id={self.id}, dataset_id={self.dataset_id}, "
            f"category='{self.category}', metric_name='{self.metric_name}', "
            f"metric_value={self.metric_value}, recorded_at={self.recorded_at})>"
        )


def create_all_tables() -> None:
    """
    Create all tables if they don't exist.
    
    Uses SQLAlchemy's create_all() to create tables based on the models.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully (or already exist)")
    except Exception as e:
        print(f"✗ Error creating tables: {str(e)}")
        raise

if __name__ == "__main__":
    create_all_tables()
    print("All tables created successfully!")