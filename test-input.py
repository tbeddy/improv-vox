"""
This script is designed to send simple data over OSC to the main program
without having to set-up your own audio retrieval system.

It is adapted from the "Simple client" example on python-osc homepage:
https://pypi.python.org/pypi/python-osc
"""

import argparse
from random import randint, shuffle
from time import sleep
from pythonosc import osc_message_builder
from pythonosc import udp_client

IP_Address = "127.0.0.1"
OSC_Port = 5005

def sendMsg(n, t, addr):
    """
    Sends a simple series of non-repeating notes (as midi numbers)
    over the designated OSC port, one note per second.
    The series is made up of four notes in a C Major chord:
    C5 (60), E5 (64), G5 (67), C6 (72)
    """    
    msg = osc_message_builder.OscMessageBuilder(address = addr)
    msg.add_arg(n)
    msg.add_arg(t)
    msg = msg.build()
    client.send(msg)

def sendNote(n):
    """
    Sends a simple series of non-repeating notes (as midi numbers)
    over the designated OSC port
    """    
    msg = osc_message_builder.OscMessageBuilder(address = "/note")
    msg.add_arg(n)
    msg = msg.build()
    client.send(msg)

def makeTwelveToneRow():
    """ Generates series of all 12 chromatic pitches from C5 to B5 in random order """
    row = [i for i in range(60,72)]
    shuffle(row)
    return row

def playPhrase(p):
    p.reverse() #reverse it then pop
    while(len(p) > 1):
        nextnote = p.pop()
        sendMsg(nextnote, 500, "/space")
        sleep(0.5)
    sleep(0.5) #total of 1 second; will recognize end of phrase
    sendMsg(p.pop(), 1000, "/space")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=IP_Address,
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=OSC_Port,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()     
    client = udp_client.UDPClient(args.ip, args.port)

    #Outlines a C Major chord starting on C5
    notes1 = [60, 64, 67, 72]
    #Lowers the two Cs to Bs, making an E Major chord in second inversion 
    notes2 = [59, 64, 67, 71]
    
    while(True):
        playPhrase(notes1)
        notes1 = [60, 64, 67, 72] #because pop emptied it...
        sleep(3)
        playPhrase(notes2)
        notes2 = [59, 64, 67, 71]
        sleep(3)
        playPhrase(makeTwelveToneRow())
        sleep(3)
