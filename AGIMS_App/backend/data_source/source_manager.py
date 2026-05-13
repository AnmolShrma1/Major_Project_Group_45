"""
Data Source Manager — single get_data(prn) entry point for the simulation loop.
Priority: Real GNSS device → CSV Dataset → Synthetic Simulator
"""
import logging
from typing import Dict, Optional

from config import GNSS_SERIAL_PORT, GNSS_BAUD_RATE, GNSS_TIMEOUT, GNSS_MOCK_API
from data_source.real_gnss_reader import RealGNSSReader, GNSSConnectionError
from data_source.dataset_loader   import DatasetLoader

logger = logging.getLogger(__name__)


class SourceMode:
    REAL      = "real"
    DATASET   = "dataset"
    SIMULATED = "simulated"


class DataSourceManager:
    """
    Arbitrates between data sources transparently.
    Falls back one level if the active source fails at runtime.
    """

    def __init__(self, simulator=None):
        """
        Args:
            simulator: GNSSDataSimulator instance used as last-resort fallback.
        """
        self.simulator  = simulator
        self._mode      = SourceMode.SIMULATED
        self._reader:   Optional[RealGNSSReader] = None
        self._dataset:  Optional[DatasetLoader]  = None
        self._init()

    # ── Init ───────────────────────────────────────────────────────────────────
    def _init(self):
        # 1 — Real device
        try:
            r = RealGNSSReader(GNSS_SERIAL_PORT, GNSS_BAUD_RATE, GNSS_TIMEOUT, GNSS_MOCK_API)
            self._reader = r
            self._mode   = SourceMode.REAL
            logger.info("[Source] REAL GNSS device connected")
            return
        except GNSSConnectionError as e:
            logger.info("[Source] Real GNSS unavailable: %s", e)

        # 2 — CSV dataset
        loader = DatasetLoader()
        if loader.is_loaded:
            self._dataset = loader
            self._mode    = SourceMode.DATASET
            logger.info("[Source] DATASET mode — %d rows, PRNs: %s",
                        loader.total_rows, loader.available_prns)
            return

        # 3 — Synthetic simulator
        logger.info("[Source] SIMULATED mode (synthetic data)")
        self._mode = SourceMode.SIMULATED

    # ── Public API ─────────────────────────────────────────────────────────────
    def get_data(self, prn: int) -> Dict[str, float]:
        """Return one feature dict for prn from the active source."""
        if self._mode == SourceMode.REAL:
            sample = self._reader.read_sample(prn)
            if sample:
                return sample
            logger.warning("[Source] Real reader returned None — falling back")
            self._mode = SourceMode.DATASET if self._dataset else SourceMode.SIMULATED

        if self._mode == SourceMode.DATASET and self._dataset:
            return self._dataset.get_sample(prn)

        # Simulated fallback
        if self.simulator:
            return self.simulator.generate_sample(prn)

        raise RuntimeError("No data source available and no simulator provided.")

    @property
    def mode(self) -> str:
        return self._mode

    def close(self):
        if self._reader:
            try: self._reader.close()
            except Exception: pass
