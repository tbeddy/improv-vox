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
from queue import Queue
from time import time
from collections import Counter
from copy import deepcopy, copy
from random import random, randint, randrange, choice, expovariate
from music21 import *
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
from note_class import MyNote

input_OSC_port = 5005
output_OSC_port = 6006

human_all_notes = []           #All notes played by the human
motif_pool_pitches = []        #Pitched motifs derived from these notes
motif_pool_durations = []      #Rhythmics motifs derived from these notes
note_queue = Queue()           #Notes queued up to be output
notelist_size = 10             #Number of notes to check when using motf_detection
motdet_pace = 5                #Number of notes passed until motif_detection is invoked
motdet_count = 0               #Moves up every time note is stored, reset once motif_detection_pace is reached
last_time = time()*1000.0      #The last time the time was checked
next_duration = 1000           #If this duration is passed, then next note will be sent to output
lowest_pitch = 45              #Lowest pitch the system is allowed to make
highest_pitch = 70             #Highest pitch the system is allowed to make


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
    new_note = MyNote(pitch,
                      quantize_duration(duration), #quantize duration before being stored
                      velocity,
                      c1, c2, c3, c4)
    print("INPUT NOTE: {}".format(new_note))
    human_all_notes.append(new_note)

def queue_next_motif(unused_addr, args):
    """
    -Picks a motif if less than 20 notes in note_queue
    -Weighted towards those motifs more recently added
    -Puts each of the notes of the motif in the global note_queue
    """
    global motif_pool_pitches, note_queue
    if (note_queue.qsize() < 20):
        motif_index = (len(motif_pool_pitches)-1) - int(len(motif_pool_pitches)*expovariate(3.0))
        selected_motif = motif_pool_pitches[motif_index]
        for current_note in selected_motif:
            note_queue.put(current_note)
        #print("QUEUED")

def retrieve_next_note(unused_addr, args):
    """
    -Pops next note from note_queue and uses send_note function on it
    """
    global next_duration, last_time
    current_time = time()*1000.0 #check the current time, multiply by 1000.0 to get milliseconds
    if (next_duration <= (current_time - last_time)):
        current_note = note_queue.get()
        #print("OUTPUT NOTE: {}".format(current_note))
        send_note(current_note)
        next_duration = note_queue.queue[0].duration #store next note's duration without popping note
        last_time = current_time

def send_note(this_note):
    """
    -Sends each of the parameters of a note as the arguments of an OSC message
    """
    msg = osc_message_builder.OscMessageBuilder(address = "/note")
    msg.add_arg(this_note.pitch)
    msg.add_arg(this_note.duration)
    #msg.add_arg(this_note.velocity)
    #msg.add_arg(this_note.mfcc[0])
    #msg.add_arg(this_note.mfcc[1])
    #msg.add_arg(this_note.mfcc[2])
    #msg.add_arg(this_note.mfcc[3])
    msg = msg.build()
    output_client.send(msg)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Analysis~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#These functions are for analyzing notes or phrases.
        
def motif_detection(notelist, parameter):
    """
    -Looks for patterns in a list of notes
    -Patterns are intended to be recognizable musical motifs, melodic or rhythmic
    -The longest pattern found more than once is returned
    -Pattern length can be anywhere from two notes to half the length of notelist
    """
    global notelist_size, human_all_notes
    if (parameter == "duration"):
        note_parameter_list = [quantize_duration(n.duration) for n in notelist]
    elif (parameter == "pitch"):
        note_parameter_list = [n.pitch for n in notelist]
    subnotelist_coll = [] #store every note sequence at least two notes long here
    for i in range(len(note_parameter_list)//2, 1, -1): #each possible sublist length
        subnotelist = []
        for j in range(0, len(note_parameter_list)-(i-1)):
            subnotelist.append(tuple(note_parameter_list[j:j+i]))
        subnotelist_coll.append(subnotelist)
    cnt = [Counter(subnotelist) for subnotelist in subnotelist_coll] #make a Counter object for each list of possible motifs
    most_common_motifs = [c.most_common(1)[0][0] for c in cnt if c.most_common(1)[0][1] > 1] #grab the most common motif from each Counter
    if most_common_motifs and (most_common_motifs[0] not in motif_pool_pitches): #save the longest motif, if the list isn't empty and hasn't been saved already
        if (parameter == "duration"):
            best_motif = []
            for d in most_common_motifs[0]:
                best_motif.append(MyNote(60, d, 60, 0.0, 0.0, 0.0, 0.0))
            motif_pool_durations.append(best_motif)
        elif (parameter == "pitch"):
            best_motif = []
            for p in most_common_motifs[0]:
                best_motif.append(MyNote(p, 500, 60, 0.0, 0.0, 0.0, 0.0))
            motif_pool_pitches.append(best_motif)
        print("DETECTED: {}".format(most_common_motifs[0]))
    
def quantize_duration(dur):
    """
    -Makes a note's duration closer to a standard set of possible notes
    -Adapted from Sven Marnach's answer to this question:
       http://stackoverflow.com/questions/9810391/round-to-the-nearest-500-python
    """
    if (dur <= 500):
        return 500
    elif (dur >= 2000):
        return 2000
    else:
        return int(round(dur / 500.0) * 500.0)

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
    global motif_pool_pitches, motif_pool_durations
    new_motif = []
    phrase_length = randint(2, 5) #random length for phrase
    for i in range(phrase_length): #generate several notes and append each to the stream
        current_note = MyNote(randint(lowest_pitch, highest_pitch), #baritone-ish voice range in MIDI values
                              randrange(500, 1501, 500), #duration already quantized
                              randint(60, 90),
                              random(), random(), random(), random())
        new_motif.append(current_note)
    motif_pool_pitches.append(new_motif)
    print("GENERATED MOTIF: {}".format(new_motif))

def permutate_motif(motif):
    """
    -Randomly apply one of the permutation functions to the motif
    """
    func_num = randint(1, 3) #don't make the tuning functions available yet
    #func_num = 4
    if (func_num == 1):
        #print("RETROGRADE")
        return retrograde(motif)
    elif (func_num == 2):
        #print("TRANSPOSE")
        return transpose(motif, randint(-3, 3)) #random interval
    elif (func_num == 3):
        #print("STRETCH/SHRINK")
        possible_degrees = [0.25, 0.5, 1.5, 2.0] #degrees of stretching/shrinking allowed
        return stretch(motif, choice(possible_degrees))
    elif (func_num == 4):
        #print("PITCH TRANSFORM")
        return transform_pitch(motif)
    elif (func_num == 5):
        #print("FLOURISH")
        return add_flourish(motif)
    elif (func_num == 6):
        return make_phrase_outoftune(motif)
    elif (func_num == 7):
        return make_phrase_intune(motif)

def retrograde(motif):
    """
    -Reverses order of notes in phrase
    -Does not alter any of notes' parameters
    """
    new_motif = []
    for i in range(len(motif)-1, -1, -1):
        new_motif.append(motif[i])
    return new_motif

def transpose(motif, interval):
    """
    -Raises every note in phrase by designated interval
    -Only alters frequency/pitch parameter
    -Interval must be an integer
    """
    new_motif = deepcopy(motif)     #make new motif from deepcopy of original motif
    for current_note in new_motif:
        current_note.pitch += interval
    return new_motif
  
def stretch(motif, degree):
    """
    -Stretches (or shrinks) phrase duration
    -Equally stretches each note
    -Use float between 0.0 and 1.0 to shrink
    -Only alters duration parameter
    """
    if (any(n.duration > 2000 for n in motif)) and (degree >= 1.0):    #don't stretch motifs with very long notes
        degree = choice([0.25, 0.5])
    elif (any(n.duration < 500 for n in motif)) and (degree <= 1.0):   #don't shrink motifs with very short notes
        #degree = choice([1.5, 2.0])
        degree = 2.0
    new_motif = deepcopy(motif)     #make new motif from deepcopy of original motif
    for current_note in new_motif:
        current_note.duration = int(current_note.duration * degree)
    return new_motif

def transform_pitch(motif):
    """
    -randomly transform one pitch
    """
    new_motif = deepcopy(motif)
    transform_point = randint(0, len(new_motif)-1)                       #pick a random point in the motif to transform
    old_pitch = new_motif[transform_point].pitch
    possible_pitches = [i for i in range(lowest_pitch, old_pitch)] + \   #pitches available (that aren't the old pitch)
                       [i for i in range(old_pitch+1, highest_pitch)]
    new_pitch = choice(possible_pitches)
    new_motif[transform_point].pitch = new_pitch
    return new_motif

def add_flourish(motif):
    """
    -Adds one note to a phrase in the same key
    """
    motif_stream = stream.Stream()                  #extract pitch info from motif into music21 stream
    for n in motif:
        current_note = note.Note()                  #create new note
        current_note.pitch.midi = n.pitch           #set note's pitch
        motif_stream.append(current_note)           #append note to stream
    this_key = motif_stream.analyze('key')
    this_scale = this_key.getScale()

    sorted_motif = sorted(motif_stream)             #sort motif (by pitch)
    lowest_note = sorted_motif[0]                   #lowest note
    highest_note = sorted_motif[-1]                 #highest note
    
    #randomly pick pitch in scale from between these two pitches
    possible_pitches = this_scale.getPitches(str(lowest_note.pitch), str(highest_note.pitch))
    new_pitch = choice(possible_pitches)

    insert_point = randint(1, len(motif)-1)         #pick a random point in the motif to insert the new note
    previous_note = motif[insert_point-1]
    following_note = motif[insert_point]
    
    new_duration = randrange(250, int(previous_note.duration/2), 250)    #make random duration for new note
    motif[insert_point-1].duration -= new_duration                #shorten duration of preceding note

    #new note's velocity is between the velocities of the notes that surround it
    lower_vel = min(previous_note.velocity, following_note.velocity)
    upper_vel = max(previous_note.velocity, following_note.velocity)
    new_velocity = randint(lower_vel, upper_vel)
    
    #create new mfcc list by randomly taking coefficients from surrounding notes
    new_mfcc = []
    for (co1, co2) in zip(previous_note.mfcc, following_note.mfcc):
        new_mfcc.append(choice([co1, co2]))
        
    new_mynote = MyNote(new_pitch.midi,             #put all the new values into a MyNote object
                        new_duration,
                        new_velocity,
                        new_mfcc[0],
                        new_mfcc[1],
                        new_mfcc[2],
                        new_mfcc[3])
    motif.insert(insert_point, new_mynote)          #insert the new note into the motif
    return deepcopy(motif)

def make_phrase_outoftune(motif, note_num):
    """
    -Randomly alters a few notes in a phrase to make them offkey
    """

def make_note_intune(note):
    """
    -Assigns any offkey notes to nearest note
    -If note is closer to neighboring note instead
    -Ex: C5 (30 cents) becomes C5 (0 cents)
         C5 (70 cents) becomes C#5 (0 cents)
         C5 (-30 cents) becomes C5 (0 cents)
         C5 (-70 cents) becomes B4 (0 cents)
    """
    new_note = deepcopy(note)
    new_note.pitch.microtone = 0
    if (note.pitch.microtone.cents >= 50):
        new_note = new_note.transpose(1)     
    elif (note.pitch.microtone.cents <= -50):
        new_note = new_note.transpose(-1)
    return new_note

def make_phrase_intune(motif):
    """
    -Applies the make_note_intune function to all notes in a phrase
    """
    new_motif = []
    for n in motif:
        new_motif.append(make_note_intune(n))
    return new_motif


#~~~~~~~~~~~~~~~~~~~~OSC Functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#These functions are only called through OSC messages.
#Their purpose is to call similarly named functions without the baggage of OSC addresses as inputs.

def osc_generate_motif(unused_addr, args):
    generate_motif()

def osc_permutate_motif(unused_addr, args):
    global motif_pool_pitches

    print("MOTIFS:")
    for m in motif_pool_pitches:
        print(m)
    
    old_motif = choice(motif_pool_pitches)
    new_motif = permutate_motif(old_motif)        #generate a new motif by permutating one of the saved motifs

    #print("SAME???? {}".format(old_motif == new_motif))
    
    while (new_motif in motif_pool_pitches):      #if the new motif has already been generated, generate a new motif
        new_motif = permutate_motif(choice(motif_pool_pitches))
    motif_pool_pitches.append(new_motif)

def osc_motif_detection(unused_addr, args):
    global human_all_notes
    notelist = human_all_notes[(-1 * notelist_size):] #grab a set number of notes last played by human
    #parameter = choice(["pitch", "duration"]) #randomly choose to look for melodic or rhythmic motifs
    parameter = "pitch"
    motif_detection(notelist, parameter)


#~~~~~~~~~~~~~~~~~~~~~Initialize~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == "__main__":
    input_parser = argparse.ArgumentParser()
    input_parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    input_parser.add_argument("--port", type=int, default=input_OSC_port, help="The port to listen on")
    input_args = input_parser.parse_args()
    
    #Dispatcher "listens" on these addresses and sends any matching information
    #to the designated function
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/note", store_new_note, "note") #receives note from input
    dispatcher.map("/motifdetection", osc_motif_detection, "note")
    dispatcher.map("/queuenextmotif", queue_next_motif, "note")
    dispatcher.map("/generatemotif", osc_generate_motif, "note")
    dispatcher.map("/retrievenextnote", retrieve_next_note, "note")
    dispatcher.map("/permutatemotif", osc_permutate_motif, "note")

    for i in range(randint(1,3)): #generate a few motifs to start out
        generate_motif()
        
    #Launches the server and continues to run until manually ended
    server = osc_server.ThreadingOSCUDPServer(
        (input_args.ip, input_args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
