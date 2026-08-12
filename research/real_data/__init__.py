"""Real-market data ingestion for ForexAI."""

from .dukascopy_ingest import DukascopyIngestError, DukascopyM1Ingestor, ingest_m1
from .manifest import build_manifest, sha256_file
from .normalizer import canonicalize_ohlcv, resample_ohlcv
from .validator import validate_ohlcv

__all__ = ["DukascopyIngestError", "DukascopyM1Ingestor", "ingest_m1", "build_manifest", "sha256_file", "canonicalize_ohlcv", "resample_ohlcv", "validate_ohlcv"]
