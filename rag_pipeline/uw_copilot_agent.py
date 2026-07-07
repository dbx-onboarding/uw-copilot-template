# DEPRECATED — This file is superseded by src/uw_copilot/agent.py
#
# This file is kept only for backwards compatibility during migration.
# All new code should import from the package:
#
#   from uw_copilot.agent import UWCopilotAgent, log_and_register_agent
#   from uw_copilot.config import Config
#   from uw_copilot.retrieval import HybridRetriever
#   from uw_copilot.guardrails import GuardrailPipeline
#
# To register and deploy the agent, use notebook 09_deploy which calls
# log_and_register_agent() from the package.

import warnings
warnings.warn(
    "rag_pipeline/uw_copilot_agent.py is deprecated. "
    "Import from uw_copilot.agent instead.",
    DeprecationWarning,
    stacklevel=2,
)

from uw_copilot.agent import UWCopilotAgent, log_and_register_agent  # noqa: F401,E402
from uw_copilot.config import Config  # noqa: F401,E402
