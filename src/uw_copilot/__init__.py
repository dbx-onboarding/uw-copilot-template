"""
uw_copilot — UW CoPilot platform library.

Install once on the cluster or via %pip install -e /path/to/repo,
then import from any notebook or app:

    from uw_copilot.config import Config
    from uw_copilot.retrieval import HybridRetriever
    from uw_copilot.guardrails import GuardrailPipeline
    from uw_copilot.session import SessionManager
    from uw_copilot.chunker import HierarchicalChunker
    from uw_copilot.agent import UWCopilotAgent
"""

from .config import Config
from .agent import UWCopilotAgent

__version__ = "0.1.0"
__all__ = ["Config", "UWCopilotAgent"]
