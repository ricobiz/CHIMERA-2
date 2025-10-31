"""
Autonomous Automation Module for Chimera AIOS
Integrates with existing services for bulletproof automation
"""

from .agent import AutonomousAgent, autonomous_agent
from .meta_planner import MetaPlanner, meta_planner
from .tactical_brain import TacticalBrain, tactical_brain
from .tools.orchestrator import ToolOrchestrator, tool_orchestrator
from .perception import Perception, perception  
from .execution import Execution, execution
from .verification import Verification, verification

__all__ = [
    'AutonomousAgent', 'autonomous_agent',
    'MetaPlanner', 'meta_planner', 
    'TacticalBrain', 'tactical_brain',
    'ToolOrchestrator', 'tool_orchestrator',
    'Perception', 'perception',
    'Execution', 'execution', 
    'Verification', 'verification'
]