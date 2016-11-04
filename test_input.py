"""
This script is designed to send simple data over OSC to the main program
without having to set-up your own audio retrieval system.

It is adapted from the "Simple client" example on python-osc homepage:
https://pypi.python.org/pypi/python-osc
"""

import argparse
from random import randint, shuffle, uniform
from time import sleep
from pythonosc import osc_message_builder
from pythonosc import udp_client

IP_Address = "127.0.0.1"
OSC_Port = 5005

def sendNote(pitch, duration, velocity, c1, c2, c3, c4):
    """
    Sends a simple series of non-repeating notes (as midi numbers)
    over the designated OSC port
    """    
    msg = osc_message_builder.OscMessageBuilder(address = "/note")
    msg.add_arg(pitch)
    msg.add_arg(duration)
    msg.add_arg(velocity)
    msg.add_arg(c1)
    msg.add_arg(c2)
    msg.add_arg(c3)
    msg.add_arg(c4)
    msg = msg.build()
    client.send(msg)

def makeTwelveToneRow():
    """ Generates series of all 12 chromatic notes from C5 to B5 in random order """
    row = [i for i in range(60,72)]
    shuffle(row)
    return [makeRandomParameters(pitch) for pitch in row]

def playPhrase(notelist):
    copyp = notelist
    length = len(copyp)
    count = 0
    for note, duration, velocity, c1, c2, c3, c4 in copyp:
        sendNote(note, duration, velocity, c1, c2, c3, c4)
        sleep(duration/1000.0)

def makeRandomParameters(pitch, duration):
    """
    -Returns an array with the designated pitch and duration and other parameters randomized 
    """
    return [pitch, duration, randint(40, 60), uniform(0.1,1.0), uniform(0.1,1.0), uniform(0.1,1.0), uniform(0.1,1.0)]
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=IP_Address,
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=OSC_Port,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()     
    client = udp_client.UDPClient(args.ip, args.port)

    #cmaj outlines a C Major chord starting on C5.
    #emin lowers the two Cs to Bs, making an E Minor chord in second inversion.
    cmaj = [makeRandomParameters(60, 1000),
            makeRandomParameters(64, 1500),
            makeRandomParameters(67, 500),
            makeRandomParameters(72, 1000)]
    emin = [makeRandomParameters(59, 1500),
            makeRandomParameters(64, 500),
            makeRandomParameters(67, 1000),
            makeRandomParameters(71, 1500)]
    
    while(True):
        playPhrase(cmaj)
        playPhrase(emin)
        #playPhrase(makeTwelveToneRow())        
