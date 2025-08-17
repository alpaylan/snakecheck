"""
SnakeCheck - A simple Hypothesis clone for property-based testing.
"""

from .composite import CompositeStrategy, composite, composite_strategy, traced_composite
from .core import given, strategy
from .generators import Strategy, booleans, choices, floats, integers, lists, strings
from .property import PropertyTest, forall
from .shrinking import DataflowAwareShrinker, shrink_with_dataflow
from .trace import GenerationTrace, TraceableDrawFn, create_traceable_draw

__version__ = "0.1.0"
__all__ = [
    "given",
    "strategy",
    "Strategy",
    "integers",
    "strings",
    "lists",
    "booleans",
    "floats",
    "choices",
    "PropertyTest",
    "forall",
    "composite",
    "composite_strategy",
    "traced_composite",
    "CompositeStrategy",
    "GenerationTrace",
    "TraceableDrawFn",
    "create_traceable_draw",
    "DataflowAwareShrinker",
    "shrink_with_dataflow",
]
