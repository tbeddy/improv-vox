# improv-vox

This is a project for real-time musical improvisation. It is built around the three part "PQf" model proposed by Blackwell et al[1]:

* P - Receives audio input and outputs symbolic notation (pitch, duration, timbre). Iimplemented in Max/MSP.
* f - Receives the symbolic notation from P and outputs symbolic notation in the same format. This is the core of this project. Written in Python 3.
* Q - Receives the symbolic notation from f and outputs synthesized sound. Written in Csound.

Included in this repo:
* a P file
* a f file
* a Q file
* a Python class file for P
* a script to launch all three components

## Installation

## Required libraries

### Max

* FTM http://ftm.ircam.fr

### Python (via pip)

* music21 http://web.mit.edu/music21/
* python-osc https://pypi.python.org/pypi/python-osc

## Usage

To use the system:

1.  Open P.maxpat (in the ear folder) in Max.
2.  Open Q.csd (in the mouth folder) in CsoundQt and press the Run button in the top left corner.
3.  In the terminal application, run f.py (in the brain folder) with Python: <code> python brain/f.py </code>


Alteratively, you can run launch_system.py to launch all three components: <code> python launch_system.py </code> Csound will instead run as a command line program.

I have only tested the system in OS X 10.11.3 El Capitan. I expect the Csound component to run fine in Windows or Linux. The Python component likely won't run correctly in Windows because it uses a Unix-only library (curses). Max is not available in a native Linux version and I expect the fragile web of externals in the component to break in Windows.

## Contributing

Because this project is a part of my undergraduate thesis work, I can't ethically accept any contributions. However, once my work for it is done academically, I would be more than happy to accept look over any pull requests for features or bugs and discuss how the project can develop. The writing accompanying the project largely resolves around the personal process of developing the software, but I'd love to see how the process develops once more minds enter the fray. If you enjoy the idea of computational creativity and improvised music, send me a message and I'd love to talk!

[1] Blackwell, Tim; Bown, Oliver; Young, Michael. Live Algorithms: Towards Autonomous Computer Improvisers. Computers and Creativity. Editied by McCormack, Jon and d'Inverno, Mark. 2016. Springer, Berlin.
