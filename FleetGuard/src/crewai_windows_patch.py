"""
Windows Patch for CrewAI
Fixes signal.SIGHUP and other signal issues on Windows by adding missing signal constants
This must be imported BEFORE importing crewai
"""

import sys
import signal

# Windows doesn't have these signals, so we add them as dummy values
if sys.platform == 'win32':
    # Add ALL missing signal constants that CrewAI expects
    # Using standard Unix signal numbers as dummy values
    signal_constants = {
        'SIGHUP': 1,      # Hangup
        'SIGINT': 2,      # Interrupt (Ctrl+C) - usually exists
        'SIGQUIT': 3,     # Quit
        'SIGILL': 4,      # Illegal instruction
        'SIGTRAP': 5,     # Trace/breakpoint trap
        'SIGABRT': 6,     # Abort
        'SIGBUS': 7,      # Bus error
        'SIGFPE': 8,      # Floating point exception
        'SIGKILL': 9,     # Kill
        'SIGUSR1': 10,    # User-defined signal 1
        'SIGSEGV': 11,    # Segmentation violation
        'SIGUSR2': 12,    # User-defined signal 2
        'SIGPIPE': 13,    # Broken pipe
        'SIGALRM': 14,    # Alarm clock
        'SIGTERM': 15,    # Termination
        'SIGSTKFLT': 16,  # Stack fault
        'SIGCHLD': 17,    # Child status changed
        'SIGCONT': 18,    # Continue
        'SIGSTOP': 19,    # Stop
        'SIGTSTP': 20,    # Terminal stop
        'SIGTTIN': 21,    # Terminal input for background process
        'SIGTTOU': 22,    # Terminal output for background process
        'SIGURG': 23,     # Urgent condition on socket
        'SIGXCPU': 24,    # CPU time limit exceeded
        'SIGXFSZ': 25,    # File size limit exceeded
        'SIGVTALRM': 26,  # Virtual alarm clock
        'SIGPROF': 27,    # Profiling timer expired
        'SIGWINCH': 28,   # Window size change
        'SIGIO': 29,      # I/O now possible
        'SIGPWR': 30,     # Power failure
        'SIGSYS': 31,     # Bad system call
    }
    
    # Add only signals that don't exist
    for sig_name, sig_value in signal_constants.items():
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, sig_value)

# Now it's safe to import crewai
# This module should be imported before any crewai imports

