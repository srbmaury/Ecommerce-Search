"""
Thread-safe and process-safe user management with file locking.
"""
import json
import os
import threading
import sys

# Import platform-specific locking module
if sys.platform == 'win32':
    import msvcrt
    USE_FCNTL = False
else:
    import fcntl
    USE_FCNTL = True

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
# Thread lock for coordinating file access across threads in the same process
_users_lock = threading.Lock()


def _lock_file(f, exclusive=False):
    """Acquire a file lock (platform-specific)."""
    if USE_FCNTL:
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(f.fileno(), lock_type)
    else:
        # Windows: msvcrt doesn't have shared locks, always exclusive
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)


def _unlock_file(f):
    """Release a file lock (platform-specific)."""
    if USE_FCNTL:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    else:
        # Windows: unlock
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def load_users():
    """Load users with file locking to prevent race conditions."""
    with _users_lock:
        # Check file existence inside lock to prevent race condition
        if not os.path.exists(USERS_FILE):
            return []
        try:
            with open(USERS_FILE, "r") as f:
                # Acquire shared lock for reading (exclusive on Windows)
                _lock_file(f, exclusive=False)
                try:
                    return json.load(f)
                finally:
                    _unlock_file(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # File was deleted or corrupted between existence check and open
            return []


def save_users(users):
    """Save users with file locking to prevent race conditions."""
    with _users_lock:
        # Use atomic write pattern: write to temp file, then rename
        temp_file = USERS_FILE + ".tmp"
        try:
            with open(temp_file, "w") as f:
                # Acquire exclusive lock for writing
                _lock_file(f, exclusive=True)
                try:
                    json.dump(users, f, indent=2)
                    f.flush()  # Ensure data is written to disk
                    os.fsync(f.fileno())  # Force write to disk
                finally:
                    _unlock_file(f)
            # Atomic rename (on POSIX systems)
            os.replace(temp_file, USERS_FILE)
        except Exception:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    # Best-effort cleanup: failure to delete the temp file is non-fatal.
                    pass
            raise
