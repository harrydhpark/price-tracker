import os
import sys
import json
import time
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
LOG_FILE = os.path.join(DATA_DIR, "scraping_logs.jsonl")
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

def emit_summary(
    country: str = "CH",
    retailer: str = "Unknown",
    brand: str = "Unknown",
    total_extracted: int = 0,
    after_year_filter: int = None,
    after_category_filter: int = None,
    final_deduplicated: int = None,
    waf_blocks: int = 0,
    parse_errors: int = 0,
    execution_time_sec: float = 0.0,
    timestamp: str = None,
    **extra
) -> None:
    """Emits a structured JSON summary line to data/scraping_logs.jsonl.
    Adheres strictly to AGENTS.md §9 schema.
    Guaranteed to never raise exceptions to avoid interrupting scraping or sync.
    """
    try:
        if after_year_filter is None:
            after_year_filter = total_extracted
        if after_category_filter is None:
            after_category_filter = after_year_filter
        if final_deduplicated is None:
            final_deduplicated = after_category_filter
        if timestamp is None:
            timestamp = datetime.now().astimezone().isoformat()

        record = {
            "country": str(country).upper(),
            "retailer": str(retailer),
            "brand": str(brand).upper(),
            "total_extracted": int(total_extracted),
            "after_year_filter": int(after_year_filter),
            "after_category_filter": int(after_category_filter),
            "final_deduplicated": int(final_deduplicated),
            "waf_blocks": int(waf_blocks),
            "parse_errors": int(parse_errors),
            "execution_time_sec": round(float(execution_time_sec), 2),
            "timestamp": str(timestamp)
        }
        if extra:
            record.update(extra)

        os.makedirs(DATA_DIR, exist_ok=True)

        # Log rollover check (10MB)
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) >= MAX_LOG_SIZE:
            rollover_target = LOG_FILE + ".1"
            try:
                if os.path.exists(rollover_target):
                    os.remove(rollover_target)
                os.rename(LOG_FILE, rollover_target)
            except Exception as re_err:
                sys.stderr.write(f"[WARN] Failed to rollover log file: {re_err}\n")

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to emit scraping log: {e}\n")
