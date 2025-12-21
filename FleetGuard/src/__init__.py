"""
FleetGuard Source Package
Contains all core modules for the FleetGuard Multi-Agent System
"""

# Suppress Streamlit warnings during module import
import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='.*ScriptRunContext.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*bare mode.*')

# Windows patch - MUST run before any crewai imports
# This fixes signal.SIGHUP and other signal issues on Windows
import sys
if sys.platform == 'win32':
    try:
        from src.crewai_windows_patch import *
    except ImportError:
        # If patch file doesn't exist, try to apply patch directly
        import signal
        if not hasattr(signal, 'SIGHUP'):
            signal.SIGHUP = 1
        if not hasattr(signal, 'SIGCONT'):
            signal.SIGCONT = 18
        if not hasattr(signal, 'SIGTSTP'):
            signal.SIGTSTP = 20
        if not hasattr(signal, 'SIGUSR1'):
            signal.SIGUSR1 = 10
        if not hasattr(signal, 'SIGUSR2'):
            signal.SIGUSR2 = 12

# Now it's safe to import crewai modules
__all__ = [
    'database_manager',
    'ai_engine',
    'crew_orchestrator',
    'crewai_agents',
    'crewai_tasks',
    'predictive_agent',
    'extractor',
]

