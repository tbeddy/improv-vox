"""
TIM'S FREE IMPROVISER
Written in Python 3.5.1

The goal of this project is to receive information that has been extracted 
from real-time monophonic audio and output similar information for use with 
a software synthesizer.

Information is received as a series of values that describe a note.
For the current version of this protocol (0.1), these are:
-pitch/frequency (float) (in range of 50.0 to 400.0)
-duration in milliseconds (int)
-velocity (int)
-MFCC (four floats)

Future features:
-Determine melodic and rhythmic motifs/patterns from input and incorporate them into output
-Develop output stream that motifs can be incorporated into
-Actually ouput the data over OSC
-Possibly develop a fixed compositional framework for the improvisation

MIT License (c) Tim Bedford
"""

import argparse
import math
from collections import Counter
from copy import deepcopy
from random import random, randint, choice, expovariate
from music21 import *
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
from note_class import MyNote
from queue import Queue

input_OSC_port = 5005
output_OSC_port = 6006

human_all_notes = [] #All notes played by the human
motif_pool = [] #All motifs derived from these notes
note_queue = Queue() #Notes queued up to be output
notelist_size = 40 #Number of notes to check when using motf_detection
motdet_pace = 5 #Number of notes passed until motif_detection is invoked
motdet_count = 0 #Moves up every time note is stored, reset once motif_detection_pace is reached


#This section is to establish the "client" (the part of the program sending
#OSC data). It will be reorganized soon, since all of these variables
#probably shouldn't be global.
output_parser = argparse.ArgumentParser()
output_parser.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
output_parser.add_argument("--port", type=int, default=output_OSC_port ,help="The port the OSC server is listening on")
output_args = output_parser.parse_args()     
output_client = udp_client.UDPClient(output_args.ip, output_args.port)

#This is the client for receiving my own messages, not outputting them to the synth
output_parser2 = argparse.ArgumentParser()
output_parser2.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
output_parser2.add_argument("--port", type=int, default=input_OSC_port ,help="The port the OSC server is listening on")
output_args2 = output_parser2.parse_args()     
input_client = udp_client.UDPClient(output_args2.ip, output_args2.port)


#~~~~~~~~~~~~~~~~~~~~~~~~~~Storing/Retrieving~~~~~~~~~~~~~~~~~~~~~~
#These functions are for storing notes and using them when needed.

def store_new_note(unused_addr, args, pitch, duration, velocity, c1, c2, c3, c4):
    """
    -Stores incoming notes in as they are received
    -Receives notes as series of seven parameters:
       -pitch
       -note duration
       -velocity
       -four coefficients derived from the mel-frequency cepstrum of the signal
    """
    global human_all_notes
    new_note = MyNote(pitch, duration, velocity, c1, c2, c3, c4)
    human_all_notes.append(new_note)
    """
    if (motdet_count == motdet_pace): #possibly trigger motif_detection function
        msg = osc_message_builder.OscMessageBuilder(address = "/motifdetection")
        msg.add_arg(human_all_notes[:-notelist_size])
        msg.add_arg("pitch")
        input_client.send(msg)
        motdet_count = 0 #reset count
    else:
        motdet_count += 1
    """

def queue_next_motif(unused_addr, args):
    """
    -Picks a motif (weighted towards those more recently added)
    -Puts each of the notes of the motif in the global note_queue
    """
    global motif_pool
    motif_index = (len(motif_pool)-1) - int(len(motif_pool)*expovariate(3.0)) #use as index to pick from motif_pool
    selected_motif = motif_pool[motif_index]
    for current_note in selected_motif:
        note_queue.put(current_note)
    print("queue!")

def retrieve_next_note():
    """
    -Pops next note from note_queue and uses send_note function on it
    """
    current_note = note_queue.get()
    send_note(current_note)
    

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~OSC Sending~~~~~~~~~~~~~~~~~~~~~~~~~~~

def send_note(this_note):
    """
    -Sends each of the parameters of a note as an OSC messagea
    """
    msg = osc_message_builder.OscMessageBuilder(address = "/note")
    msg.add_arg(this_note.pitch)
    msg.add_arg(this_note.duration)
    msg.add_arg(this_note.velocity)
    msg.add_arg(this_note.mfcc[0])
    msg.add_arg(this_note.mfcc[1])
    msg.add_arg(this_note.mfcc[2])
    msg.add_arg(this_note.mfcc[3])
    msg = msg.build()
    output_client.send(msg)
    

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Analysis~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#These functions are for analyzing notes or phrases.
        
def motif_detection(unused_addr, args, notelist, parameter):
    """
    -Looks for patterns in a list of notes
    -Patterns are intended to be recognizable musical motifs, melodic or rhythmic
    -The longest pattern found more than once is returned
    -Pattern length can be anywhere from two notes to half the length of notelist
    """
    if (parameter == "duration"):
        note_parameter_list = [n.duration for n in notelist]
    elif (parameter == "pitch"):
        note_parameter_list = [n.pitch for n in notelist]
    subnotelist_coll = []
    for i in range(len(note_parameter_list)//2, 1, -1): #each possible sublist length
        subnotelist_coll.append([str(x[j:j+i]) for j in range(0, len(note_parameter_list)-(i-1))])
    cnt = [Counter(minilist) for minilist in subnotelist_coll] #make a Counter object for each list of possible motifs
    most_common_motifs = [Counter(c).most_common(1) for c in cnt] #grab the most common from each Counter
    most_common_motifs = [motif for motif in most_common_motifs if (motif[1] > 1)] #remove any motifs that are only found once
    if most_common_motifs: #save the longest motif, if the list isn't empty
        motif_pool.append(most_common_motifs[0])
    print("detect!")

def quantize_note(note):
    """
    -Makes a note's duration closer to a standard set of possible notes
    """
    possible_notes = [50,100,200,400,600,1000,1500,2000,3000,4000,8000]

def key_of_phrase(phrase):
    """
    -Determines key of phrase
    """
    key = phrase.analyze('key')
    return [key.tonic.name, key.mode]
              
def phrase_to_stream(nums):
    stream1 = stream.Stream()
    for i in nums:
        stream1.append(note.Note(midiNumToNote(i)))
    return stream1

def midi_num_to_note(i):
    x = pitch.Pitch()
    x.midi = i
    return x.nameWithOctave

def pitch_range(phrase):
    """ 
    -Finds range between highest and lowest pitch in phrase
    """
    fe = features.jSymbolic.RangeFeature(phrase)
    return fe.extract().vector[0]


#~~~~~~~~~~~~~~~~~~~~~~~~Generative Functions~~~~~~~~~~~~~~~~~~~~~~
#These functions are for the purpose of generating new material.

def generate_motif():
    """
    -Creates randomized motif
    -Should have no relation to anything the vocalist is doing
    """
    new_motif = stream.Stream()
    phrase_length = randint(2, 8) #random length for phrase
    for i in range(phraselist): #generate several notes and append each to the stream
        current_note = MyNote() #blank instance of MyNote class
        current_note.pitch = randint(33, 57) #baritone-ish voice range in MIDI values
        current_note.duration = randint(100, 1000)
        current_note.velocity = randint(60, 90)
        current_note.mfcc = [random() for i in range(4)]

def permutate_phrase(phrase):
    """
    -Randomly apply one of the permutation functions to the phrase
    """
    func_num = randint(1, 7)
    if (func_num == 1):
        return retrograde(phrase)
    elif (func_num == 2):
        return transpose(phrase, randint(-3, 3)) #random interval
    elif (func_num == 3):
        return invert(phrase)
    elif (func_num == 4):
        possible_degrees = [0.25, 0.5, 1.5, 2.0, 3.0] #degrees of stretching/shrinking allowed
        return stretch(phrase, choice(possible_degrees))
    elif (func_num == 5):
        return add_flourish(phrase)
    elif (func_num == 6):
        return make_phrase_outoftune(phrase)
    elif (func_num == 7):
        return make_phrase_intune(phrase)

def retrograde(phrase):
    """
    -Reverses order of notes in phrase
    -Does not alter any of notes' parameters
    """
    new_phrase = stream.Stream()
    for i in range(len(phrase)-1, -1, -1):
        new_phrase.append(phrase[i]) #use the music21 insert function, not Python insert
    return new_phrase

def transpose(phrase, interval):
    """
    -Raises every note in phrase by designated interval
    -Only alters frequency/pitch parameter
    -Interval is an integer
    """
    new_phrase = stream.Stream()
    for note in phrase:
        new_phrase.append(note.transpose(interval))
    return new_phrase

def invert(phrase):
    """
    -Starts on intial note
    -Next note is inversion of interval
    -Ex: C4 to E4 (4 semitones) becomes C4 to G#3 (-4 semitones)
    -Only alters frequency/pitch parameter (and not for first note)
    """
    
def stretch(phrase, degree):
    """
    -Stretches (or shrinks) phrase duration
    -Equally stretches each note
    -Use float between 0.0 and 1.0 to shrink
    -Only alters duration parameter
    """
    new_phrase = stream.Stream()
    for note in phrase:
        dur = note.duration.quarterLength
        n = note #make a copy of the note
        n.duration = duration.Duration(degree * dur)
        new_phrase.append(n)
    return new_phrase

def add_flourish(phrase):
    """
    -Adds at least one note to a phrase  
    """

def make_phrase_outoftune(phrase, note_num):
    """
    -Randomly alters a few notes in a phrase to make them offkey
    """

def make_note_intune(note1):
    """
    -Assigns any offkey notes to nearest note
    -If note is closer to neighboring note instead
    -Ex: C5 (30 cents) becomes C5 (0 cents)
         C5 (70 cents) becomes C#5 (0 cents)
         C5 (-30 cents) becomes C5 (0 cents)
         C5 (-70 cents) becomes B4 (0 cents)
    """
    note2 = deepcopy(note1)
    note2.pitch.microtone = 0
    if (note1.pitch.microtone.cents >= 50):
        note2 = note2.transpose(1)     
    elif (note1.pitch.microtone.cents <= -50):
        note2 = note2.transpose(-1)
    return note2

def make_phrase_intune(phrase):
    """
    -Applies the make_note_intune function to all notes in a phrase
    """
    new_phrase = stream.Stream()
    for note in phrase:
        new_phrase.append(make_note_intune(note))
    return new_phrase


#~~~~~~~~~~~~~~~~~~~~~Initialize~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    input_parser = argparse.ArgumentParser()
    input_parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    input_parser.add_argument("--port",
                        type=int, default=input_OSC_port, help="The port to listen on")
    input_args = input_parser.parse_args()
    #Dispatcher "listens" on these addresses and sends any matching information
    #to the designated function
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/note", store_new_note, "note") #receives note from input
    dispatcher.map("/motifdetection", motif_detection, "note")
    dispatcher.map("/queuenextmotif", queue_next_motif, "note")
    dispatcher.map("/generatemotif", generate_motif, "note")
    dispatcher.map("/retrievenextnote", retrieve_next_note, "note")
        
    #Launches the server and continues to run until manually ended
    server = osc_server.ThreadingOSCUDPServer(
        (input_args.ip, input_args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
