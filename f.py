"""
Written in Python 3.5.1

The goal of this file is to receive information that has been extracted
from real-time monophonic audio and output similar information for use with
a software synthesizer.

Information is received as a series of values that describe a note.
For the current version of this protocol, these are:
-pitch/frequency (float) (in range of 50.0 to 400.0)
-duration in milliseconds (int)
-velocity (int)
-formants (four integers)

MIT License (c) Tim Bedford
"""

# Standard library
import argparse
import math
import curses
import signal
import sys
from queue import Queue
from time import time
from collections import Counter
from copy import deepcopy
from random import random, randint, randrange, choice, expovariate, uniform

# Third party
from music21 import *
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client

# Project specific
from note_class import MyNote

input_OSC_port = 5005          # The OSC port to receive data from P
output_OSC_port = 6006         # The OSC port to send data to Q
lowest_pitch = 45              # Lowest pitch the system is allowed to make
highest_pitch = 70             # Highest pitch the system is allowed to make
f1min = 250
f1max = 700
f2min = 550
f2max = 1900
f3min = 2550
f3max = 2850
f4min = 2750
f4max = 3250
f5min = 3000
f5max = 3600

human_all_notes = []           # All notes played by the human
motif_pool_pitches = []        # Pitched motifs derived from these notes
motif_pool_durations = []      # Rhythmics motifs derived from these notes
note_queue = Queue()           # Notes queued up to be output
notelist_size = 10             # Number of notes to check when using motif_detection
last_time = time()*1000.0      # The last time the time was checked
next_duration = 1000           # If this duration is passed, then next note will be sent to output


# ~~~~~~~~~~~~~~~~~~~~~~~~~~Storing/Retrieving~~~~~~~~~~~~~~~~~~~~~~
# These functions are for storing notes and using them when needed.


def store_new_note(unused_addr, pitch, duration, velocity, f1, f2, f3, f4, f5):
    """Store incoming notes as they are received.

    Notes are received as eight arguments
    pitch (int): this should exist as the first
    duration (int)
    The final five values
    """
    global human_all_notes
    new_note = MyNote(int(pitch),
                      quantize_duration(duration),
                      velocity,
                      f1, f2, f3, f4, f5)
    human_all_notes.append(new_note)
    input_to_screen(new_note)


def queue_next_motif(unused_addr):
    """
    -Picks a motif if less than 5 notes in note_queue
    -Weighted towards those motifs more recently added
    -Puts each of the notes of the motif in the global note_queue
    """
    global motif_pool_pitches, note_queue
    repetitions = randint(2, 7)
    if (note_queue.qsize() < 5):
        motif_index = (len(motif_pool_pitches)-1) - int(len(motif_pool_pitches)*expovariate(3.0))
        selected_motif = motif_pool_pitches[motif_index]
        for i in range(repetitions):
            for current_note in selected_motif:
                note_queue.put(current_note)
        queue_to_screen("{}/{}".format(motif_index, len(motif_pool_pitches)))


def retrieve_next_note(unused_addr):
    """Pop the next note from note_queue and apply send_note function to it."""
    global next_duration, last_time, note_queue
    current_time = time()*1000.0  # Check the current time, multiply by 1000.0 to get milliseconds
    if (next_duration <= (current_time - last_time)):
        current_note = note_queue.get()
        next_duration = current_note.duration
        send_note(current_note)
        output_to_screen(current_note)
        last_time = time()*1000.0


def send_note(this_note):
    """Send each of the parameters of a note as the arguments of an OSC message."""
    msg = osc_message_builder.OscMessageBuilder(address="/note")
    msg.add_arg(this_note.pitch)
    msg.add_arg(this_note.duration)
    msg.add_arg(this_note.velocity)
    msg.add_arg(this_note.timbre[0])
    msg.add_arg(this_note.timbre[1])
    msg.add_arg(this_note.timbre[2])
    msg.add_arg(this_note.timbre[3])
    msg.add_arg(this_note.timbre[4])
    msg = msg.build()
    output_client.send(msg)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Analysis~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# These functions are for analyzing notes or phrases.


def motif_detection(notelist, parameter):
    """
    -Looks for patterns in a list of notes
    -Patterns are intended to be recognizable musical motifs, melodic or rhythmic
    -The longest pattern found more than once is returned
    -Pattern length can be anywhere from two notes to half the length of notelist
    """
    global notelist_size, human_all_notes, motif_pool_pitches
    if (parameter == "duration"):
        note_parameter_list = [n.duration for n in notelist]
    elif (parameter == "pitch"):
        note_parameter_list = [n.pitch for n in notelist]
    subnotelist_coll = []
    for i in range(len(note_parameter_list)//2, 1, -1):  # Each possible sublist length
        subnotelist = []
        for j in range(0, len(note_parameter_list)-(i-1)):
            subnotelist.append(tuple(note_parameter_list[j:j+i]))
        subnotelist_coll.append(subnotelist)
    cnt = [Counter(subnotelist) for subnotelist in subnotelist_coll]                          # Make a Counter object for each list of possible motifs
    most_common_motifs = [c.most_common(1)[0][0] for c in cnt if c.most_common(1)[0][1] > 1]  # Grab the most common motif from each Counter
    if most_common_motifs and (most_common_motifs[0] not in motif_pool_pitches):              # Save the longest motif, if the list isn't empty and hasn't been saved already
        if (parameter == "duration"):
            best_motif = []
            for d in most_common_motifs[0]:
                best_motif.append(MyNote(60, d, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            motif_pool_durations.append(best_motif)
        elif (parameter == "pitch"):
            best_motif = []
            for p in most_common_motifs[0]:
                best_motif.append(MyNote(p, 500, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            motif_pool_pitches.append(best_motif)
        return best_motif
    else:
        return []


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


# ~~~~~~~~~~~~~~~~~~~~~~~~Generative Functions~~~~~~~~~~~~~~~~~~~~~~
# These functions are for the purpose of generating new material.


def generate_motif():
    """
    -Creates randomized motif
    -Should have no relation to anything the vocalist is doing
    """
    global motif_pool_pitches, motif_pool_durations
    new_motif = []
    phrase_length = randint(2, 5)                                    # Random length for phrase
    for i in range(phrase_length):                                   # Generate several notes and append each to the stream
        current_note = MyNote(randint(lowest_pitch, highest_pitch),  # Voice range in MIDI values
                              randrange(500, 1501, 500),             # Duration already quantized
                              uniform(1.0, 1.0),
                              randint(f1min, f1max),
                              randint(f2min, f2max),
                              randint(f3min, f3max),
                              randint(f4min, f4max),
                              randint(f5min, f5max))
        new_motif.append(current_note)
    motif_pool_pitches.append(new_motif)
    motif_to_screen(new_motif)


def permutate_motif(motif):
    """
    -Randomly apply one of the permutation functions to the motif
    """
    func_num = randint(1, 4)                      # (Don't make the tuning functions available yet)
    if (func_num == 1):
        return retrograde(motif)
    elif (func_num == 2):
        return transpose(motif, randint(-3, 3))   # Random interval
    elif (func_num == 3):
        possible_degrees = [0.25, 0.5, 1.5, 2.0]  # Degrees of stretching/shrinking allowed
        return stretch(motif, choice(possible_degrees))
    elif (func_num == 4):
        return transform_pitch(motif)
    elif (func_num == 5):
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
    new_motif = deepcopy(motif)     # Make new motif from deepcopy of original motif
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
    if (any(n.duration > 2000 for n in motif)) and (degree >= 1.0):    # Don't stretch motifs with very long notes
        degree = choice([0.25, 0.5])
    elif (any(n.duration < 500 for n in motif)) and (degree <= 1.0):   # Don't shrink motifs with very short notes
        degree = 2.0
    new_motif = deepcopy(motif)                                        # Make new motif from deepcopy of original motif
    for current_note in new_motif:
        current_note.duration = int(current_note.duration * degree)
    return new_motif


def transform_pitch(motif):
    """
    -Randomly transforms one pitch
    """
    new_motif = deepcopy(motif)
    transform_point = randint(0, len(new_motif)-1)                       # Pick a random point in the motif to transform
    old_pitch = new_motif[transform_point].pitch
    possible_pitches = ([i for i in range(lowest_pitch, old_pitch)] +    # Pitches available (that aren't the old pitch)
                        [i for i in range(old_pitch+1, highest_pitch)])
    new_pitch = choice(possible_pitches)
    new_motif[transform_point].pitch = new_pitch
    return new_motif


def add_flourish(motif):
    """
    -Adds one note to a phrase in the same key
    """
    motif_stream = stream.Stream()                  # Extract pitch info from motif into music21 stream
    for n in motif:
        current_note = note.Note()                  # Create new note
        current_note.pitch.midi = n.pitch           # Set note's pitch
        motif_stream.append(current_note)           # Append note to stream
    this_key = motif_stream.analyze('key')
    this_scale = this_key.getScale()

    sorted_motif = sorted(motif_stream)             # Sort motif (by pitch)
    lowest_note = sorted_motif[0]                   # Lowest note
    highest_note = sorted_motif[-1]                 # Highest note

    # Randomly pick pitch in scale from between these two pitches
    possible_pitches = this_scale.getPitches(str(lowest_note.pitch), str(highest_note.pitch))
    new_pitch = choice(possible_pitches)

    insert_point = randint(1, len(motif)-1)         # Pick a random point in the motif to insert the new note
    previous_note = motif[insert_point-1]
    following_note = motif[insert_point]

    new_duration = randrange(250, int(previous_note.duration/2), 250)    # Make random duration for new note
    motif[insert_point-1].duration -= new_duration                       # Shorten duration of preceding note

    # New note's velocity is between the velocities of the notes that surround it
    lower_vel = min(previous_note.velocity, following_note.velocity)
    upper_vel = max(previous_note.velocity, following_note.velocity)
    new_velocity = randint(lower_vel, upper_vel)

    # Create new mfcc list by randomly taking coefficients from surrounding notes
    new_mfcc = []
    for (co1, co2) in zip(previous_note.mfcc, following_note.mfcc):
        new_mfcc.append(choice([co1, co2]))

    new_mynote = MyNote(new_pitch.midi,             # Put all the new values into a MyNote object
                        new_duration,
                        new_velocity,
                        new_mfcc[0],
                        new_mfcc[1],
                        new_mfcc[2],
                        new_mfcc[3])
    motif.insert(insert_point, new_mynote)          # Insert the new note into the motif
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


# ~~~~~~~~~~~~~~~~~~~~OSC Functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# These functions are only called through OSC messages.
# Their purpose is to call similarly named functions without the baggage of OSC addresses as inputs.


def osc_generate_motif(unused_addr):
    generate_motif()


def osc_permutate_motif(unused_addr):
    global motif_pool_pitches

    old_motif = choice(motif_pool_pitches)
    new_motif = permutate_motif(old_motif)        # Generate a new motif by permutating one of the saved motifs

    while (new_motif in motif_pool_pitches):      # If the new motif has already been generated, generate a new motif
        new_motif = permutate_motif(choice(motif_pool_pitches))

    motif_pool_pitches.append(new_motif)
    motif_to_screen(new_motif)


def osc_motif_detection(unused_addr):
    global human_all_notes, motif_pool_pitches
    notelist = human_all_notes[(-1 * notelist_size):]  # Grab a set number of notes last played by human
    #parameter = choice(["pitch", "duration"])         # Randomly choose to look for melodic or rhythmic motifs
    parameter = "pitch"
    new_motif = motif_detection(notelist, parameter)

    if new_motif:                                   # If motif_detection was able to find a new motif...
        motif_pool_pitches.append(new_motif)        # ...store it...
        detect_to_screen(new_motif)                 # ...and print it to the window


# ~~~~~~~~~~~~~~~~~~~~~~~Curses~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# These functions are for managing the pseudo-GUI


def info_check(s):
    info_win.addstr("{}".format(s))
    info_win.refresh()


def setup_window(window, title):
    window.border()
    window.addstr(1, (term_width//8)-3, title)
    window.move(2, 1)


def motif_to_screen(motif):
    cur_y, cur_x = motif_win.getyx()            # Grab the cursor's current x and y positions
    motif_win.addstr(cur_y, cur_x, str(motif))  # Print the motif to the window
    motif_win.move(cur_y+1, cur_x)              # Move the cursor to the next line for next time
    motif_win.border()                          # Re-draw the border
    motif_win.refresh()                         # Refresh the window


def detect_to_screen(motif):
    cur_y, cur_x = filler_win.getyx()
    filler_win.addstr(cur_y, cur_x, str(motif))
    filler_win.move(cur_y+1, cur_x)
    filler_win.border()
    filler_win.refresh()


def input_to_screen(note):
    input_win.deleteln()
    input_win.insertln()
    input_win.addstr(2, 1, str(note))
    input_win.border()
    input_win.refresh()


def output_to_screen(note):
    output_win.deleteln()
    output_win.insertln()
    output_win.addstr(2, 1, str(note))
    output_win.border()
    output_win.refresh()


def queue_to_screen(q):
    queue_win.deleteln()
    queue_win.insertln()
    queue_win.addstr(2, 1, q)
    queue_win.border()
    queue_win.refresh()


def signal_handler(signal, frame):
    """
    -Ends curses and then the entire program
    -Adapted from Johan Kotlinski's answer to this question:
        -https://stackoverflow.com/questions/4205317/capture-keyboardinterrupt-in-python-without-try-except
    """
    curses.endwin()
    sys.exit(0)


# ~~~~~~~~~~~~~~~~~~~~~Initialize~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == "__main__":
    stdscr = curses.initscr()      # Initialize curses
    curses.noecho()
    curses.cbreak()
    term_height = curses.LINES     # Terminal height
    term_width = curses.COLS       # Terminal width

    # Create several subwindows to visualize data in the terminal
    input_win = stdscr.subwin(   term_height//4,     term_width//4, 0,              0)
    output_win = stdscr.subwin(  term_height//4,     term_width//4, term_height//4, 0)
    motif_win = stdscr.subwin(   (term_height*7)//8, term_width//4, 0,              term_width//4)
    filler_win = stdscr.subwin(  (term_height*7)//8, term_width//4, 0,              term_width//2)
    info_win = stdscr.subwin(    term_height//4,     term_width//4, term_height//2, 0)
    queue_win = stdscr.subwin(   (term_height*7)//8, term_width//4, 0,              (term_width*3)//4)

    # Setup each window (border, title).
    setup_window(input_win, "Input")
    setup_window(output_win, "Output")
    setup_window(motif_win, "Motifs")
    setup_window(filler_win, "Filler")
    setup_window(queue_win, "Queue")
    setup_window(info_win, "Info")

    # Print the OSC addresses in info_win.
    cur_y, cur_x = info_win.getyx()
    info_win.addstr("Listening to port {}".format(input_OSC_port))
    info_win.move(cur_y+1, cur_x)
    info_win.addstr("Sending to port {}".format(output_OSC_port))
    info_win.move(cur_y+3, cur_x)
    info_win.addstr("Press Ctrl-C to stop program.")
    info_win.move(cur_y+4, cur_x)
    info_win.addstr("If using launch_system.py,")
    info_win.move(cur_y+5, cur_x)
    info_win.addstr("Ctrl-C will also end Csound.")

    # Make all the changes to curses visible.
    stdscr.refresh()

    # This section is to establish the "client" (the part of the program sending OSC data)
    output_parser = argparse.ArgumentParser()
    output_parser.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
    output_parser.add_argument("--port", type=int, default=output_OSC_port, help="The port the OSC server is listening on")
    output_args = output_parser.parse_args()
    output_client = udp_client.UDPClient(output_args.ip, output_args.port)

    """
    #This is the client for receiving my own messages, not outputting them to the synth
    output_parser2 = argparse.ArgumentParser()
    output_parser2.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
    output_parser2.add_argument("--port", type=int, default=input_OSC_port ,help="The port the OSC server is listening on")
    output_args2 = output_parser2.parse_args()
    input_client = udp_client.UDPClient(output_args2.ip, output_args2.port)
    """

    input_parser = argparse.ArgumentParser()
    input_parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    input_parser.add_argument("--port", type=int, default=input_OSC_port, help="The port to listen on")
    input_args = input_parser.parse_args()

    # Dispatcher "listens" on these addresses and sends any matching information
    # to the designated function.
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/note", store_new_note)
    dispatcher.map("/motifdetection", osc_motif_detection)
    dispatcher.map("/queuenextmotif", queue_next_motif)
    dispatcher.map("/generatemotif", osc_generate_motif)
    dispatcher.map("/retrievenextnote", retrieve_next_note)
    dispatcher.map("/permutatemotif", osc_permutate_motif)

    # Create server.
    server = osc_server.ThreadingOSCUDPServer(
        (input_args.ip, input_args.port), dispatcher)

    # Generate a few motifs to start out.
    for i in range(randint(1, 3)):
        generate_motif()

    signal.signal(signal.SIGINT, signal_handler)

    # Launch the server.
    server.serve_forever()
