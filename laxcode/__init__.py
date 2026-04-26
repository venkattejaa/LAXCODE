"""
LAXCODE - Agentic AI Coding Agent
Powered by Laxmana AI with NVIDIA NIM API support
"""

__version__ = "1.1.0"
__author__ = "LAXCODE Team"
__email__ = "venkattejaa@gmail.com"

from .core.agent import LaxcodeAgent
from .core.session import Session

__all__ = ["LaxcodeAgent", "Session"]
