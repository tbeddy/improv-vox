# improv-vox

This is a project for real-time musical improvisation. It is built around the three part "PfQ" model proposed by Blackwell et al[1]:

* P - Receives audio input and outputs symbolic notation (pitch, duration, timbre). I have implemented this in Max/MSP.
* f - Receives the symbolic notation from P and outputs symbolic notation in the same format. This is the core of this project and written in Python 3.
* Q - Receives the symbolic notation from f and outputs synthesized sound.

Included in this repo are a test script, an image of my current Max/MSP set-up, and the f file.

## Required libraries

* music21 http://web.mit.edu/music21/
* python-osc https://pypi.python.org/pypi/python-osc

Both are available via pip.

## Contributing

Because this project is a part of my undergraduate thesis work, I can't ethically accept any contributions. However, once my work for it is done academically, I would be more than happy to accept look over any pull requests for features or bugs and discuss how the project can develop. The writing accompanying the project largely resolves around the personal process of developing the software, but I'd love to see how the process develops once more minds enter the fray. If you enjoy the idea of computational creativity and improvised music, send me a message and I'd love to talk!

[1] Blackwell, Tim; Bown, Oliver; Young, Michael. Live Algorithms: Towards Autonomous Computer Improvisers. Computers and Creativity. Editied by McCormack, Jon and d'Inverno, Mark. 2016. Springer, Berlin.