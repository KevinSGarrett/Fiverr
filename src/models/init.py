"""Compatibility exports for legacy `src.models.init` imports."""

from src.models.search_result import SearchResult, get_latest_search_result, write_search_result  # noqa: F401
from src.models import *  # noqa: F403
