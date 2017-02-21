# improv-vox

This is a project for real-time musical improvisation. It is built around the three part "PfQ" model proposed by Blackwell et al[1]:

* P - Receives audio input and outputs symbolic notation (pitch, duration, timbre). Iimplemented in Max/MSP.
* f - Receives the symbolic notation from P and outputs symbolic notation in the same format. This is the core of this project. Written in Python 3.
* Q - Receives the symbolic notation from f and outputs synthesized sound. Written in Csound.

Included in this repo:
* a P file
* a f file
* a Q file
* a test script (to mimic P)
* a Python class file for P

## Required libraries

* music21 http://web.mit.edu/music21/
* python-osc https://pypi.python.org/pypi/python-osc

Both are available via pip.

## Usage

To use the system:
1. Run the file P.maxpat in Max.
2. Run the file Q.csd in Csound
3. Run the file f.py in your terminal.

## TODO
* Make OSC usage in f more consistent
* Finish implementing curses
* Make the docs/comments more consistent and pretty
* Implement rhythmic motifs
* Regularly delete motifs
* Make P more user-friendly for those who can't edit Max files
* Write a script to launch P, f, and Q
* Make usage curses optional (with a flag?)
* Get output and input parsers out of global namespace

## Contributing

Because this project is a part of my undergraduate thesis work, I can't ethically accept any contributions. However, once my work for it is done academically, I would be more than happy to accept look over any pull requests for features or bugs and discuss how the project can develop. The writing accompanying the project largely resolves around the personal process of developing the software, but I'd love to see how the process develops once more minds enter the fray. If you enjoy the idea of computational creativity and improvised music, send me a message and I'd love to talk!

[1] Blackwell, Tim; Bown, Oliver; Young, Michael. Live Algorithms: Towards Autonomous Computer Improvisers. Computers and Creativity. Editied by McCormack, Jon and d'Inverno, Mark. 2016. Springer, Berlin.