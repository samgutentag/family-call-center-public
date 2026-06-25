import yaml


def load_yaml(path):
    """Load a YAML file into Python data, or None if the file is missing."""
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None
