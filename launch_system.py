"""
Run this file to start the system.
"""

import subprocess

max_commands = ["open", "-a", "Max", "ear/P.maxpat"]
csound_commands = ["csound", "-o", "dac", "-d", "mouth/Q.csd"]
python_commands = ["python", "brain/f.py"]

launch_max = subprocess.run(max_commands)
launch_csound = subprocess.Popen(csound_commands)
launch_python = subprocess.run(python_commands)
