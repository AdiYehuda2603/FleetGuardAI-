"""
Suppress Streamlit ScriptRunContext warnings
This module should be imported before any Streamlit code
"""
import warnings
import logging
import os

# Suppress Python warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Suppress Streamlit logger warnings
logging.getLogger('streamlit.runtime.scriptrunner.script_runner').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.caching').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.state').setLevel(logging.ERROR)
logging.getLogger('streamlit').setLevel(logging.ERROR)

# Set environment variable to suppress warnings
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'




