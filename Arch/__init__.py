"""
Smart Home Agent AI Architectures

This package contains different AI architecture implementations for smart home automation:
- Standard: Direct single-shot approach
- CoT: Chain of Thought with step-by-step reasoning
- ReAct: Reasoning and Acting with iterative cycles
- Reflexion: Self-reflection and error correction
- ToT: Tree of Thoughts with multiple reasoning paths
"""

from .standard import call_agent as standard_call
from .cot import call_agent as cot_call
from .react import call_agent as react_call
from .reflexion import call_agent as reflexion_call
from .tot import call_agent as tot_call

__all__ = [
    'standard_call',
    'cot_call', 
    'react_call',
    'reflexion_call',
    'tot_call'
]
