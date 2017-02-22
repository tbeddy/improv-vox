"""
Run this file to start the system.
"""

import subprocess

max_commands = ["open", "-a", "Max", "P.maxpat"]
csound_commands = ["csound", "-o", "dac", "-d", "Q.csd"]
python_commands = ["python", "f.py"]

launch_max = subprocess.run(max_commands)
launch_csound = subprocess.Popen(csound_commands)
launch_python = subprocess.run(python_commands)
