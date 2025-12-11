"""
Pattern Detection Module

This module provides tools for collecting and analyzing pattern signals
from git history, agent memories, and code churn to identify anti-patterns
and improvement opportunities in the codebase.

Modules:
- collect: Collects pattern signals from git history, agent memory, and code churn
- analyze: Uses Claude AI to identify patterns from collected signals
"""

__version__ = "1.0.0"

from .collect import (
    GitHistoryAnalyzer,
    AgentMemoryAnalyzer,
    CodeChurnAnalyzer,
    collect_all_signals,
)

from .analyze import (
    PatternAnalyzer,
)

__all__ = [
    'GitHistoryAnalyzer',
    'AgentMemoryAnalyzer',
    'CodeChurnAnalyzer',
    'collect_all_signals',
    'PatternAnalyzer',
]
