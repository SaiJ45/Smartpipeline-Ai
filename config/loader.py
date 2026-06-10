import yaml
from pathlib import Path
from typing import Dict, Any


def load_dataset_config(dataset_name: str) -> Dict[str, Any]:
    """
    Load dataset configuration from config/dataset_config.yaml.
    
    Args:
        dataset_name: Name of the dataset to load
        
    Returns:
        Dictionary containing the dataset configuration
        
    Raises:
        FileNotFoundError: If dataset_config.yaml is not found
        KeyError: If the specified dataset is not found in the config
    """
    config_path = Path(__file__).parent / "dataset_config.yaml"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dataset configuration file not found at {config_path}. "
            "Please ensure config/dataset_config.yaml exists."
        )
    
    if not config or "datasets" not in config:
        raise ValueError(
            f"Invalid dataset configuration file. "
            "Expected 'datasets' key in {config_path}"
        )
    
    datasets = config.get("datasets", {})
    
    if dataset_name not in datasets:
        available_datasets = list(datasets.keys())
        raise KeyError(
            f"Dataset '{dataset_name}' not found in configuration. "
            f"Available datasets: {available_datasets}"
        )
    
    return datasets[dataset_name]


def get_active_dataset() -> Dict[str, Any]:
    """
    Get the active dataset configuration.
    
    Reads the 'active_dataset' field from config/dataset_config.yaml
    and returns that dataset's configuration.
    
    Returns:
        Dictionary containing the active dataset configuration
        
    Raises:
        FileNotFoundError: If dataset_config.yaml is not found
        KeyError: If active_dataset is not specified or the dataset is not found
    """
    config_path = Path(__file__).parent / "dataset_config.yaml"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dataset configuration file not found at {config_path}. "
            "Please ensure config/dataset_config.yaml exists."
        )
    
    if not config or "active_dataset" not in config:
        raise KeyError(
            f"'active_dataset' field not found in {config_path}. "
            "Please specify which dataset is active."
        )
    
    active_name = config.get("active_dataset")
    dataset = load_dataset_config(active_name)
    dataset['name'] = active_name
    dataset['active_dataset'] = active_name
    
    return dataset
