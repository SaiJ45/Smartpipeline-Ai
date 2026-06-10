from config.loader import get_active_dataset
from ingestion.loader import DataLoader

def main():
    config = get_active_dataset()

    print("Starting data ingestion...")
    loader = DataLoader()
    loader.load_all(config)
    print('Done!')

if __name__ == "__main__":
    main()
