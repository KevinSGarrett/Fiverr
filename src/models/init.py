"""Compatibility exports for legacy `src.models.init` imports."""

from src.models import *  # noqa: F403
from src.models.external_signal import (  # noqa: F401
    ExternalSignal,
    get_all_signals,
    get_signal,
    write_external_signal,
)
from src.models.search_result import (  # noqa: F401
    SearchResult,
    get_latest_search_result,
    write_search_result,
)
