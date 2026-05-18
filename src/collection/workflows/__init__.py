"""Collection workflow classes — one workflow per file, per .cursorrules.

Each workflow wraps the corresponding functional module and exposes a
standard ``run()`` interface that the collection orchestrator calls.
Importing this package registers all workflow classes.
"""

from src.collection.workflows.auto_promotion import AutoPromotionWorkflow
from src.collection.workflows.autocomplete import AutocompleteWorkflow
from src.collection.workflows.fiverr_search import FiverrSearchWorkflow
from src.collection.workflows.gig_detail import GigDetailWorkflow
from src.collection.workflows.google_trends import GoogleTrendsWorkflow
from src.collection.workflows.keyword_expansion import (
    KeywordExpansionWorkflow,
    run_keyword_expansion_stub,
)
from src.collection.workflows.niche_init import run_niche_initialization
from src.collection.workflows.reddit_signals import RedditSignalWorkflow
from src.collection.workflows.seller_profile import SellerProfileWorkflow

__all__ = [
    "AutoPromotionWorkflow",
    "AutocompleteWorkflow",
    "FiverrSearchWorkflow",
    "GigDetailWorkflow",
    "GoogleTrendsWorkflow",
    "KeywordExpansionWorkflow",
    "RedditSignalWorkflow",
    "SellerProfileWorkflow",
    "run_niche_initialization",
    "run_keyword_expansion_stub",
]
