"""
CSV Dataset Loader — streams Cleaned_GPS_Spoofing_Dataset.csv row by row.

Expected columns (case-insensitive): PRN, DO, PD, CN0, TCD, EC, LC, PC
Optional column:  OUTPUT (0=normal, 1=spoofed) — logged for stats only
Extra columns:    RX, TOW, CP, PIP, PQP — silently ignored
"""
import logging
import os
from collections import defaultdict
from typing import Dict, List

import numpy as np

from config import DATASET_PATH, FEATURE_RANGES

logger = logging.getLogger(__name__)

REQUIRED = {"DO", "PD", "CN0", "TCD", "EC", "LC", "PC"}


class DatasetLoader:
    """Round-robin CSV streamer, one feature dict per get_sample(prn) call."""

    def __init__(self, path: str = DATASET_PATH):
        self.path    = path
        self._rows:    Dict[int, List[dict]] = defaultdict(list)
        self._cursors: Dict[int, int]        = defaultdict(int)
        self._labels:  Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._loaded   = False
        self._total    = 0
        self._load()

    # ── Internal ───────────────────────────────────────────────────────────────
    def _load(self):
        if not os.path.exists(self.path):
            logger.warning("Dataset not found: %s — synthetic fallback active.", self.path)
            return
        try:
            import pandas as pd
            logger.info("Loading dataset: %s", self.path)
            df = pd.read_csv(self.path)
            df.columns = [c.strip().upper() for c in df.columns]

            missing = REQUIRED - set(df.columns)
            if missing:
                logger.warning("Dataset missing columns %s — synthetic fallback.", missing)
                return

            has_prn    = "PRN"    in df.columns
            has_output = "OUTPUT" in df.columns

            for _, row in df.iterrows():
                try:
                    feat  = {f: float(row[f]) for f in REQUIRED}
                    prn   = int(row["PRN"]) if has_prn else 0
                    label = int(row["OUTPUT"]) if has_output else -1
                    self._rows[prn].append(feat)
                    if has_output and label >= 0:
                        self._labels[prn][label] += 1
                except Exception:
                    continue

            self._total  = sum(len(v) for v in self._rows.values())
            self._loaded = self._total > 0

            if self._loaded:
                logger.info("Dataset ready: %d rows, PRNs: %s", self._total, sorted(self._rows))
                for prn, c in self._labels.items():
                    logger.info("  PRN %2d — normal: %d  spoofed: %d", prn, c.get(0,0), c.get(1,0))
            else:
                logger.warning("Dataset empty after parsing.")

        except ImportError:
            logger.error("pandas not installed — run: pip install pandas")
        except Exception as e:
            logger.error("Dataset load error: %s", e)

    # ── Public ─────────────────────────────────────────────────────────────────
    def get_sample(self, prn: int) -> Dict[str, float]:
        """Next row for prn (round-robin). Synthetic if prn has no rows."""
        rows = self._rows.get(prn) or self._rows.get(0, [])
        if not rows:
            return self._synthetic()
        idx = self._cursors[prn] % len(rows)
        self._cursors[prn] += 1
        return dict(rows[idx])

    def _synthetic(self) -> Dict[str, float]:
        return {f: float(np.random.uniform(*r)) for f, r in FEATURE_RANGES.items()}

    @property
    def is_loaded(self) -> bool:   return self._loaded
    @property
    def total_rows(self) -> int:   return self._total
    @property
    def available_prns(self) -> list: return sorted(self._rows)

    def label_stats(self) -> Dict:
        return {p: {"normal": c.get(0,0), "spoofed": c.get(1,0)} for p, c in self._labels.items()}
