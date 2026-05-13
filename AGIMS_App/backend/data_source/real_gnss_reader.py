"""
Real GNSS device reader.
Attempts serial (NMEA) then mock-API. Raises GNSSConnectionError on failure.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GNSSConnectionError(Exception):
    """Raised when no real GNSS source is reachable."""


class RealGNSSReader:
    """
    Reads live GNSS features from:
      1. Serial port  (NMEA $PAGNSS or $GPGSV sentences)
      2. Mock REST API endpoint (JSON response with feature keys)
    Raises GNSSConnectionError if neither source responds.
    """

    def __init__(self, serial_port: str, baud_rate: int, timeout: int, mock_api: str):
        self.serial_port = serial_port
        self.baud_rate   = baud_rate
        self.timeout     = timeout
        self.mock_api    = mock_api
        self._serial     = None
        self._use_api    = False
        self._connected  = False
        self._try_connect()

    # ── Connection ─────────────────────────────────────────────────────────────
    def _try_connect(self):
        if self._try_serial():
            logger.info("Real GNSS: serial %s", self.serial_port)
            self._connected = True
            return
        if self._try_api():
            logger.info("Real GNSS: mock API %s", self.mock_api)
            self._use_api   = True
            self._connected = True
            return
        raise GNSSConnectionError(
            f"No GNSS source (serial={self.serial_port}, api={self.mock_api})"
        )

    def _try_serial(self) -> bool:
        try:
            import serial
            conn = serial.Serial(self.serial_port, baudrate=self.baud_rate, timeout=self.timeout)
            line = conn.readline().decode("ascii", errors="replace").strip()
            if line.startswith("$"):
                self._serial = conn
                return True
            conn.close()
        except Exception as e:
            logger.debug("Serial failed: %s", e)
        return False

    def _try_api(self) -> bool:
        try:
            import urllib.request
            r = urllib.request.urlopen(self.mock_api, timeout=self.timeout)
            return r.status == 200
        except Exception as e:
            logger.debug("API failed: %s", e)
        return False

    # ── Reading ────────────────────────────────────────────────────────────────
    def read_sample(self, prn: int) -> Optional[Dict[str, float]]:
        if self._serial:
            return self._read_serial(prn)
        if self._use_api:
            return self._read_api(prn)
        return None

    def _read_serial(self, prn: int) -> Optional[Dict[str, float]]:
        try:
            for _ in range(10):
                raw = self._serial.readline().decode("ascii", errors="replace").strip()
                f   = self._parse_nmea(raw, prn)
                if f:
                    return f
        except Exception as e:
            logger.warning("Serial read: %s", e)
        return None

    def _read_api(self, prn: int) -> Optional[Dict[str, float]]:
        try:
            import urllib.request, json
            with urllib.request.urlopen(f"{self.mock_api}?prn={prn}", timeout=self.timeout) as r:
                return self._validate(json.loads(r.read()))
        except Exception as e:
            logger.warning("API read: %s", e)
        return None

    def _parse_nmea(self, sentence: str, prn: int) -> Optional[Dict[str, float]]:
        try:
            if sentence.startswith("$PAGNSS"):
                p = sentence.split("*")[0].split(",")
                if int(p[1]) != prn:
                    return None
                return {"DO": float(p[2]), "PD": float(p[3]), "CN0": float(p[4]),
                        "TCD": float(p[5]), "EC": float(p[6]), "LC": float(p[7]), "PC": float(p[8])}
            if sentence.startswith("$GPGSV"):
                p = sentence.split("*")[0].split(",")
                for i in range(4, len(p) - 3, 4):
                    if p[i] == str(prn) and p[i + 3]:
                        return {"CN0": float(p[i + 3])}
        except Exception:
            pass
        return None

    def _validate(self, data: dict) -> Optional[Dict[str, float]]:
        required = {"DO", "PD", "CN0", "TCD", "EC", "LC", "PC"}
        try:
            return {k: float(data[k]) for k in required}
        except Exception:
            return None

    def close(self):
        if self._serial:
            try: self._serial.close()
            except Exception: pass
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
