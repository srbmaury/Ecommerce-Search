import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def get_data_path(filename):
    """Return the absolute path to a data file in the data directory."""
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string")

    # Disallow absolute paths
    if os.path.isabs(filename):
        raise ValueError("Absolute paths are not allowed")

    # Normalize and ensure no path traversal outside DATA_DIR
    candidate = os.path.normpath(os.path.join(DATA_DIR, filename))
    data_dir_norm = os.path.normpath(DATA_DIR) + os.sep

    # Ensure the resulting path is actually within DATA_DIR
    # The path must start with data_dir_norm to be contained within it
    if not (candidate + os.sep).startswith(data_dir_norm):
        raise ValueError("Path traversal detected")

    return candidate