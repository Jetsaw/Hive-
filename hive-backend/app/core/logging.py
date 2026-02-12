import logging
import logging.handlers
import os


def setup_logging():
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    handlers = [logging.StreamHandler()]

    # Also log to hive.log file with rotation
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "hive.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers,
    )
