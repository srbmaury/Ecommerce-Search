"""
Shared lock for CSV file operations to prevent race conditions.
"""
import threading

# Lock for CSV file operations to prevent race conditions
csv_lock = threading.Lock()