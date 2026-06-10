
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import get_active_dataset
from ingestion.loader import DataLoader


def main():
    print(f"\n{'='*50}")
    print(f"SmartPipeline AI — Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    config = get_active_dataset()
    print(f"Active dataset: {config.get('display_name', 'Unknown')}")

    print("\nStarting data ingestion...")
    loader = DataLoader()
    loader.load_all(config)

    print("\nGenerating data quality report...")
    try:
        from ingestion.quality_report import DataQualityReporter
        from database.connection import SessionLocal
        from database.models import PipelineRun

        reporter = DataQualityReporter()
        db = SessionLocal()

        runs = db.query(PipelineRun).order_by(
            PipelineRun.run_at.desc()
        ).limit(20).all()

        load_results = []
        seen = set()
        for run in runs:
            if run.source_file not in seen:
                seen.add(run.source_file)
                name = run.source_file.replace(
                    '_dataset.csv', ''
                ).replace('.csv', '')
                load_results.append({
                    "table_name": f"olist_{name}",
                    "records_in": run.records_in or 0,
                    "records_out": run.records_out or 0,
                    "records_rejected": run.records_rejected or 0,
                    "rejected_rows": [],
                    "df_sample": None
                })

        db.close()

        if load_results:
            report_path = reporter.generate(load_results)
            print(f"Quality report saved: {report_path}")
        else:
            print("No pipeline runs found for report")

    except Exception as e:
        print(f"Warning: Could not generate quality report: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*50}")
    print("Pipeline complete!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()