import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
from sqlalchemy import inspect
from pathlib import Path
import logging

from database.connection import SessionLocal, engine
from database.models import Dataset, PipelineRun
from core.schema_detector import SchemaDetector
from core.validator_factory import ValidatorFactory
from ingestion.transformer import DataTransformer

# Setup logging
logger = logging.getLogger(__name__)

# Date columns that need datetime conversion
DATE_COLUMNS = {
    'orders': [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ],
    'reviews': ['review_creation_date']
}


class DataLoader:
    """Loads Olist CSV files into PostgreSQL database."""
    
    def __init__(self, data_dir: str = "data/raw"):
        """
        Initialize the DataLoader.
        
        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        self.engine = engine
        self.records_processed = 0
        self.dataset_id = None
        self.last_rejected_rows = []
    
    def load_all(self, config: Dict[str, Any]) -> None:
        """
        Load all Olist CSV files from config into PostgreSQL.
        
        Args:
            config: Configuration dict with 'files' key containing list of:
                   {'name': table_name, 'path': file_path}
        """
        files = config.get("files", [])
        
        if not files:
            logger.warning("No files specified in config")
            return
        
        # Ensure dataset record exists
        self._ensure_dataset_exists(config)
        
        for file_config in files:
            table_name = file_config.get("name")
            file_path = file_config.get("path")
            
            if not table_name or not file_path:
                logger.warning(f"Skipping invalid file config: {file_config}")
                continue
            
            self._load_file(table_name, file_path)
    
    def _load_file(self, table_name: str, file_path: str) -> None:
        """
        Load a single CSV file into PostgreSQL.
        
        Args:
            table_name: Name of the target table
            file_path: Path to CSV file (relative to data_dir)
        """
        full_path = self.data_dir / file_path
        
        if not full_path.exists():
            logger.error(f"File not found: {full_path}")
            return
        
        logger.info(f"Loading {table_name} from {full_path}")
        print(f"\n📥 Loading {table_name}...")
        
        records_in = 0
        records_out = 0
        start_time = datetime.now()
        db_table_name = f'olist_{table_name}'
        rejected_rows_all = []
        schema = None
        validator_model = None
        transformer = DataTransformer()
        schema_detector = SchemaDetector()
        validator_factory = ValidatorFactory()
        self.last_rejected_rows = []
        
        try:
            # Read CSV in chunks
            chunk_iterator = pd.read_csv(full_path, chunksize=10000, low_memory=False)
            
            for chunk in chunk_iterator:
                # Track input records
                records_in += len(chunk)
                
                # Clean the chunk
                cleaned_chunk = self._clean_chunk(chunk, table_name)
                
                # Special handling for olist_orders
                if table_name == "orders":
                    cleaned_chunk = self._calculate_delivery_delay(cleaned_chunk)

                # Build validation schema/model from the first cleaned chunk only
                if schema is None:
                    schema = schema_detector.detect(cleaned_chunk, table_name)
                    validator_model = validator_factory.build(schema)

                valid_df, rejected_rows = transformer.transform(
                    cleaned_chunk,
                    table_name,
                    schema,
                    validator_model
                )
                rejected_rows_all.extend(rejected_rows)
                
                # Insert valid rows to database
                if not valid_df.empty:
                    try:
                        for col in valid_df.select_dtypes(
                            include=['datetime64[ns]']
                            ).columns:
                            valid_df[col] = valid_df[col].astype(object).where(
                                valid_df[col].notna(), other=None)

        
                        valid_df.to_sql(
                            db_table_name,
                            con=self.engine,
                            if_exists='append',
                            index=False,
                            chunksize=1000
                            )
                        records_out += len(valid_df)

                    except Exception as e:
                        logger.error(f"Error inserting chunk into {db_table_name}: {e}")
                        print(f"  ⚠ Insert error for {db_table_name}: {str(e)[:100]}")
                
                # Print progress every 10000 rows
                if records_out > 0 and records_out % 10000 == 0:
                     print(f"✓ Loaded {records_out:,} rows into {db_table_name}...")
                     
             
            
            self.last_rejected_rows = rejected_rows_all

            print(f"✓ Loaded {records_out:,} rows into {db_table_name} (Total: {records_in:,})")
            
            # Calculate stats
            duration_secs = (datetime.now() - start_time).total_seconds()
            throughput_rps = records_out / duration_secs if duration_secs > 0 else 0
            records_rejected = len(rejected_rows_all)
            rejection_rate = (records_rejected / records_in * 100) if records_in > 0 else 0
            
            # Insert pipeline run record
            self._insert_pipeline_run(
                table_name,
                file_path,
                records_in,
                records_out,
                records_rejected,
                rejection_rate,
                duration_secs,
                throughput_rps,
                "SUCCESS"
            )
            
        except Exception as e:
            logger.error(f"Error loading {table_name}: {e}")
            print(f"✗ Error loading {table_name}: {e}")
            self._insert_pipeline_run(
                table_name,
                file_path,
                0,
                0,
                0,
                0.0,
                0.0,
                0.0,
                "FAILED",
                str(e)
            )
    
    def _ensure_dataset_exists(self, config: Dict[str, Any]) -> None:
        """
        Check if dataset record exists. If not, create it.
        
        Stores the dataset_id as self.dataset_id for use in pipeline_run records.
        
        Args:
            config: Configuration dict with dataset info
        """
        db = SessionLocal()
        
        try:
            # Get dataset info from config
            dataset_name = config.get("dataset_name") or config.get("active_dataset") or "unknown"
            display_name = config.get("display_name", dataset_name)
            source_type = config.get("source_type", "csv")
            
            # Check if dataset already exists
            existing = db.query(Dataset).filter(Dataset.name == dataset_name).first()
            
            if existing:
                self.dataset_id = existing.id
                logger.info(f"Using existing dataset: {dataset_name} (ID: {self.dataset_id})")
            else:
                # Create new dataset record
                new_dataset = Dataset(
                    name=dataset_name,
                    display_name=display_name,
                    source_type=source_type
                )
                db.add(new_dataset)
                db.commit()
                self.dataset_id = new_dataset.id
                logger.info(f"Created new dataset: {dataset_name} (ID: {self.dataset_id})")
                print(f"✓ Dataset created: {dataset_name}")
        
        except Exception as e:
            logger.error(f"Error ensuring dataset exists: {e}")
            db.rollback()
            self.dataset_id = None
        
        finally:
            db.close()
    
    def _clean_chunk(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Clean a chunk of data.
        
        Applies transformations:
        - Strip whitespace from string columns
        - Convert date columns to datetime
        - Fill NaN in string columns with empty string
        - Fill NaN in numeric columns with 0
        
        Args:
            df: DataFrame chunk to clean
            table_name: Name of the table (for date column lookup)
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Get date columns for this table
        date_cols = DATE_COLUMNS.get(table_name, [])
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            if col not in date_cols:
                df[col] = df[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
        
        # Convert date columns to datetime
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Fill NaN values
        string_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        df[string_cols] = df[string_cols].fillna("")
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        return df
    
    def _calculate_delivery_delay(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate delivery_delay_days for olist_orders.
        
        Calculates difference between order_delivered_customer_date
        and order_estimated_delivery_date in days.
        
        Args:
            df: DataFrame with order data
            
        Returns:
            DataFrame with delivery_delay_days column added/updated
        """
        df = df.copy()
        
        if 'order_delivered_customer_date' in df.columns and 'order_estimated_delivery_date' in df.columns:
            df['delivery_delay_days'] = (
                df['order_delivered_customer_date'] - df['order_estimated_delivery_date']
            ).dt.days
        
        return df
    
    def _insert_pipeline_run(
        self,
        source_file: str,
        file_path: str,
        records_in: int,
        records_out: int,
        records_rejected: int,
        rejection_rate: float,
        duration_secs: float,
        throughput_rps: float,
        status: str,
        error_message: str = None
    ) -> None:
        """
        Insert a pipeline run record into the database.
        
        Args:
            source_file: Name of the source table/file
            file_path: Path to the source file
            records_in: Total records read
            records_out: Records successfully inserted
            records_rejected: Records failed/rejected
            rejection_rate: Percentage of rejected records
            duration_secs: Total execution time in seconds
            throughput_rps: Records per second throughput
            status: Execution status (SUCCESS/FAILED)
            error_message: Error message if failed
        """
        db = SessionLocal()
        
        try:
            # Create pipeline run record using cached dataset_id
            run = PipelineRun(
                dataset_id=self.dataset_id,
                source_file=file_path,
                records_in=records_in,
                records_out=records_out,
                records_rejected=records_rejected,
                rejection_rate=round(rejection_rate, 2),
                duration_secs=round(duration_secs, 2),
                throughput_rps=round(throughput_rps, 2),
                status=status,
                error_message=error_message
            )
            
            db.add(run)
            db.commit()
            logger.info(f"Pipeline run recorded: {source_file} - {status}")
        
        except Exception as e:
            logger.error(f"Error recording pipeline run: {e}")
            db.rollback()
        
        finally:
            db.close()
