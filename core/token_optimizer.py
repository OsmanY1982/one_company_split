"""桥接存根: core.token_optimizer → iqra.core.token_optimizer"""

from iqra.core.token_optimizer import TokenSaverMode

# agent_bridge 期望 TokenOptimizer
TokenOptimizer = TokenSaverMode
