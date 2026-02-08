from datetime import datetime, timezone
import threading

EVENT_THRESHOLD_MODEL = 500
EVENT_THRESHOLD_CLUSTERS = 200
MAX_INTERVAL_MODEL = 24 * 60 * 60
MAX_INTERVAL_CLUSTERS = 6 * 60 * 60
