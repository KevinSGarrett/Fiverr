"""
automation/report_synthesis/__init__.py
RSF-1: Public API for the report_synthesis package.
"""
from automation.report_synthesis.synthesizer import synthesize_cycle, load_cycle_synthesis
from automation.report_synthesis.directive_generator import (
    generate_directives,
    persist_directives,
    load_next_cycle_directives,
)

__all__ = [
    "synthesize_cycle",
    "load_cycle_synthesis",
    "generate_directives",
    "persist_directives",
    "load_next_cycle_directives",
]
