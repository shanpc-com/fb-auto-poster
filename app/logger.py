from __future__ import annotations
import logging
from pathlib import Path

def setup_logger(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    logger=logging.getLogger("fbposter"); logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt=logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        sh=logging.StreamHandler(); sh.setFormatter(fmt); logger.addHandler(sh)
        fh=logging.FileHandler(log_dir/"latest.log", encoding="utf-8"); fh.setFormatter(fmt); logger.addHandler(fh)
    return logger
