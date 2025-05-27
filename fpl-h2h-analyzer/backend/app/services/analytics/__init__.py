"""
Analytics package for FPL H2H Analyzer.

This package contains specialized analytics modules for advanced FPL analysis:
- DifferentialAnalyzer: Point swing contribution and differential analysis
- PredictiveEngine: ML-based match outcome predictions
- ChipAnalyzer: Strategic chip usage recommendations
- PatternRecognition: Historical pattern analysis
"""

from .differential_analyzer import DifferentialAnalyzer
from .predictive_engine import PredictiveEngine
from .chip_analyzer import ChipAnalyzer
from .pattern_recognition import PatternRecognition

__all__ = [
    'DifferentialAnalyzer',
    'PredictiveEngine',
    'ChipAnalyzer',
    'PatternRecognition'
]