import time

import schedule

from config.loader import get_active_dataset
from ingestion.loader import DataLoader
from ingestion.quality_report import DataQualityReporter


def run_pipeline() -> None:
    """Run the ingestion pipeline and generate a data quality report."""
    try:
        config = get_active_dataset()

        loader = DataLoader()
        load_results = loader.load_all(config) or []

        reporter = DataQualityReporter()
        report_path = reporter.generate(load_results)

        print(f"Quality report generated: {report_path}")
    except Exception as e:
        print(f"Pipeline failed: {e}")


schedule.every().day.at("08:00").do(run_pipeline)


def start_scheduler() -> None:
    """Start the scheduler loop."""
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    print("Scheduler started - pipeline will run daily at 08:00")
    start_scheduler()
