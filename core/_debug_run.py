"""Debug wrapper - redirects all print to a log file."""
import sys
import os

# Redirect stdout and stderr to a log file
log_path = '/tmp/iqra_debug2.log'
sys.stdout = open(log_path, 'w', buffering=1)
sys.stderr = sys.stdout

# Import and run main
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import main
