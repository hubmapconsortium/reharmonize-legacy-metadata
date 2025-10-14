"""
json-rules-engine: A library for applying conditional JSON patches.

This library provides functionality for loading and applying JSON patches
conditionally based on logical rules using __must__ (AND) and __should__ (OR)
operators.
"""

from json_rules_engine.applier import PatchApplier
from json_rules_engine.exceptions import PatchError
from json_rules_engine.patches import Patches

__version__ = "1.0.0"
__all__ = ["Patches", "PatchApplier", "PatchError"]
