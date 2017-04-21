"""
The goal of this file is to receive information that has been extracted
from real-time monophonic audio and output similar information for use with
a software synthesizer.

Written in Python 3.5.1
MIT License (c) Tim Bedford
"""

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

from music21 import *
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client

from note_class import MyNote

input_OSC_port = 5005          # The OSC port to receive data from P
output_OSC_port = 6007         # The OSC port to send data to Q
lowest_pitch = 45              # Lowest pitch the system is allowed to make
highest_pitch = 70             # Highest pitch the system is allowed to make
f1min = 250; f1max = 700
f2min = 550; f2max = 1900
f3min = 2550; f3max = 2850
f4min = 2750; f4max = 3250
f5min = 3000; f5max = 3600

human_pitches = []             # All notes played by the human
human_durations = []
motif_pool_pitches = []        # Pitched motifs derived from these notes
motif_pool_durations = []      # Rhythmics motifs derived from these notes
pitch_queue = Queue()          # Notes queued up to be output
duration_queue = Queue()
notelist_size = 20             # Number of notes to check when using motif_detection
last_time = time()*1000.0      # The last time the time was checked
next_duration = 1000           # If this duration is passed, then next note will be sent to output


# ~~~~~~~~~~~~~~~~~~~~~~~~~~Storing/Retrieving~~~~~~~~~~~~~~~~~~~~~~
# These functions are for storing notes and using them when needed.


def store_new_note(unused_addr, pitch, duration, amplitude, f1, f2, f3, f4, f5):
    """Store incoming notes as they are received.

    The note is stored in the global list human_all_notes in the custom class
    MyNote. It is then displayed in its own window in the curses interface.

    f1 through f5 are input as separate arguments because of problems with the
    program sending values to this program. If those problems are fixed, those
    five arguments will likely be rewritten as a single list.

    Arguments (various parameters of the note):
      pitch (int): This should be in MIDI pitch format.
         e.g. 60 (equivalent to C5)
      duration (int): This should be in milliseconds(ms). It will be quantized
         (i.e. rounded to the nearest 500 ms) before being stored.
         e.g. 850 (equivalent to 0.850 seconds)
         This will be stored as 1000.
      amplitude (float): This can be thought of as the note's volume. It can
         be any value from 0.0 (complete silence).
         to 1.0 (full volume).
         e.g. 0.7
      f1, f2, f3, f4, f5 (int): These five formants represent the note's timbre.
         e.g. 300, 1000, 2600, 3000, 3400

    Returns:
      None
    """
    global human_pitches, human_durations
    new_note = MyNote(int(pitch),
                      quantize_duration(duration),
                      amplitude,
                      f1, f2, f3, f4, f5)
    human_pitches.append(int(pitch))
    human_durations.append(duration)
    input_to_screen(new_note)


def queue_next_motif():
    """Queue the next motif to be sent to Q.

    If only 10 notes are in pitch_queue, one of the motifs in motif_pool_pitches
    is selected and each note is individually added to pitch_queue. More recent
    motifs are more likely to be selected.

    Once rhythmic motifs are added, this function will become more complicated
    as it will have to create truly new notes, not just notes with all but one
    of their parameters fixed.

    Arguments:
      None

    Returns:
      None
    """
    global motif_pool_pitches, pitch_queue, motif_pool_durations, duration_queue
    if (pitch_queue.qsize() < 10):
        motif_index = (len(motif_pool_pitches)-1) - int(len(motif_pool_pitches)*expovariate(3.0))
        selected_motif = motif_pool_pitches[motif_index]
        repetitions = randint(1, 6)
        for i in range(repetitions):
            for current_note in selected_motif:
                pitch_queue.put(current_note)
    if (duration_queue.qsize() < 10):
        motif_index = (len(motif_pool_durations)-1) - int(len(motif_pool_durations)*expovariate(3.0))
        selected_motif = motif_pool_durations[motif_index]
        repetitions = randint(1, 6)
        for i in range(repetitions):
            for current_note in selected_motif:
                duration_queue.put(current_note)


def retrieve_next_note():
    """Output the next note in the queue.

    If the current note has finished sounding, then the next note in pitch_queue
    is sent to Q and displayed in its own window in the curses interface.

    This function should be called from outside the program as often as possible.

    Arguments:
      None

    Returns:
      None
    """
    global next_duration, last_time, pitch_queue, duration_queue
    current_time = time()*1000.0  # Convert from seconds to milliseconds
    if (next_duration <= (current_time - last_time)):
        current_pitch = pitch_queue.get()
        current_duration = duration_queue.get()
        next_duration = current_duration
        send_note(current_pitch, current_duration, 1.0, f1min, f2min, f3min, f4min, f5min)
        output_to_screen("P: {}, D: {}".format(current_pitch, current_duration))
        last_time = time()*1000.0


def send_note(pitch, duration, amplitude, f1, f2, f3, f4, f5):
    """Send a note to Q.

    Each of the parameters of the note are individually added as arguments
    to an OSC message.

    Arguments:
      this_note(MyNote)

    Returns:
      None
    """
    msg = osc_message_builder.OscMessageBuilder(address="/note")
    msg.add_arg(pitch)
    msg.add_arg(duration)
    msg.add_arg(amplitude)
    msg.add_arg(f1)
    msg.add_arg(f2)
    msg.add_arg(f3)
    msg.add_arg(f4)
    msg.add_arg(f5)
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
    global motif_pool_pitches, motif_pool_durations
    subnotelist_coll = []
    for i in range(len(notelist)//2, 1, -1):  # Each possible sublist length
        subnotelist = []
        for j in range(0, len(notelist)-(i-1)):
            subnotelist.append(tuple(notelist[j:j+i]))
        subnotelist_coll.append(subnotelist)
    cnt = [Counter(subnotelist) for subnotelist in subnotelist_coll]                          # Make a Counter object for each list of possible motifs
    most_common_motifs = [c.most_common(1)[0][0] for c in cnt if c.most_common(1)[0][1] > 1]  # Grab the most common motif from each Counter

    # Save the longest motif, if the list isn't empty and hasn't been saved already
    if (parameter == "pitch"):
        if most_common_motifs and (most_common_motifs[0] not in motif_pool_pitches):
            best_motif = []
            for p in most_common_motifs[0]:
                best_motif.append(p)
                motif_pool_pitches.append(best_motif)
                detect_to_screen(best_motif)
            return best_motif
        else:
            return []
    elif (parameter == "duration"):
        if most_common_motifs and (most_common_motifs[0] not in motif_pool_durations):
            best_motif = []
            for d in most_common_motifs[0]:
                best_motif.append(d)
                motif_pool_durations.append(best_motif)
                detect_to_screen(best_motif)
            return best_motif
        else:
            return []


def quantize_duration(dur):
    """Quantize the duration to the nearest 500 milliseconds.

    This function was adapted from Sven Marnach's answer to this question:
       http://stackoverflow.com/questions/9810391/round-to-the-nearest-500-python

    Arguments:
      dur(int)

    Returns:
      An int
    """
    if (dur <= 500):
        return 500
    elif (dur >= 2000):
        return 2000
    else:
        return int(round(dur / 500.0) * 500.0)


# ~~~~~~~~~~~~~~~~~~~~~~~~Generative Functions~~~~~~~~~~~~~~~~~~~~~~
# These functions are for the purpose of generating new material.


def generate_motif(parameter):
    """Generate a random motif.

    Add a new motif to motif_pool_pitches. The motif is two to five notes long
    and all of the notes' parameters are randomized. The motif should have no
    relation to anything the vocalist is doing.

    Arguments:
      None

    Returns:
      None
    """
    global motif_pool_pitches, motif_pool_durations
    new_motif = []
    phrase_length = randint(2, 5)
    if (parameter == "pitch"):
        for i in range(phrase_length):
            new_motif.append(randint(lowest_pitch, highest_pitch))
        motif_pool_pitches.append(new_motif)
        motif_to_screen(new_motif, "pitch")
    elif (parameter == "duration"):
        for i in range(phrase_length):
            new_motif.append(randrange(500, 1501, 500))
        motif_pool_durations.append(new_motif)
        motif_to_screen(new_motif, "duration")


def permutate_motif(motif, parameter):
    """Randomly apply one of the permutation functions to a motif.

    Arguments:
      motif(list of MyNotes)

    Returns:
      A list of MyNotes
    """
    if (parameter == "pitch"):
        func_num = choice([1, 2, 4])
    elif (parameter == "duration"):
        func_num = choice([1, 3])

    if (func_num == 1):
        return retrograde(motif)
    elif (func_num == 2):
        return transpose(motif, randint(-3, 3))   # Random interval
    elif (func_num == 3):
        return stretch(motif, choice([0.25, 0.5, 1.5, 2.0]))
    elif (func_num == 4):
        return transform_pitch(motif)
    elif (func_num == 5):
        return add_flourish(motif)
    elif (func_num == 6):
        return make_phrase_outoftune(motif)
    elif (func_num == 7):
        return make_phrase_intune(motif)


def retrograde(motif):
    """Reverse the order of notes in a motif.

    None of the notes' parameters are altered.

    Arguments:
      motif(list of MyNotes)

    Returns:
      A list of MyNotes
    """
    new_motif = []
    for i in range(len(motif)-1, -1, -1):
        new_motif.append(motif[i])
    return new_motif


def transpose(motif, interval):
    """Raise every note in a motif by a designated interval.

    Only the notes' pitch parameters are altered.

    Arguments:
      motif(list of MyNotes)
      interval(int)

    Returns:
      A list of MyNotes
    """
    new_motif = [(i + interval) for i in motif]
    return new_motif


def stretch(motif, degree):
    """Uniformly stretch (or shrink) motif.

    Every note is stretched/shrunk the same degree. Only the notes' duration
    parameter is altered.

    Arguments:
      motif(list of MyNotes)
      degree(float)

    Returns:
      A list of MyNotes
    """
    if (any(n > 2000 for n in motif)) and (degree >= 1.0):    # Don't stretch motifs with very long notes
        degree = choice([0.25, 0.5])
    elif (any(n < 500 for n in motif)) and (degree <= 1.0):   # Don't shrink motifs with very short notes
        degree = 2.0
    new_motif = [int(dur * degree) for dur in motif]
    return new_motif


def transform_pitch(motif):
    """Randomly transform the pitch of one note in a motif.

    The new pitch can be anywhere from lowest_pitch to highest_pitch, as long
    as it isn't the same as the old pitch.

    Arguments:
      motif(list of MyNotes)

    Returns:
      A list of MyNotes
    """
    transform_point = randint(0, len(motif)-1)
    old_pitch = motif[transform_point]
    possible_pitches = ([i for i in range(lowest_pitch, old_pitch)] +
                        [i for i in range(old_pitch+1, highest_pitch)])
    new_pitch = choice(possible_pitches)
    motif[transform_point] = new_pitch
    return motif


def add_flourish(motif):
    """Add one note to a phrase in the same key."""
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
    generate_motif(choice("pitch", "duration"))


def osc_queue_next_motif(unused_addr):
    queue_next_motif()


def osc_retrieve_next_note(unused_addr):
    retrieve_next_note()


def osc_permutate_motif(unused_addr):
    global motif_pool_pitches, motif_pool_durations

    old_motif = choice(motif_pool_pitches)
    new_motif = permutate_motif(old_motif, "pitch")        # Generate a new motif by permutating one of the saved motifs
    while (new_motif in motif_pool_pitches):      # If the new motif has already been generated, generate a new motif
        new_motif = permutate_motif(choice(motif_pool_pitches), "pitch")
    motif_pool_pitches.append(new_motif)
    motif_to_screen(new_motif, "pitch")

    old_motif = choice(motif_pool_durations)
    new_motif = permutate_motif(old_motif, "duration")        # Generate a new motif by permutating one of the saved motifs
    while (new_motif in motif_pool_durations):      # If the new motif has already been generated, generate a new motif
        new_motif = permutate_motif(choice(motif_pool_durations), "duration")
    motif_pool_durations.append(new_motif)
    motif_to_screen(new_motif, "duration")


def osc_motif_detection(unused_addr):
    global human_pitches, motif_pool_pitches, human_durations, motif_pool_durations

    pitchlist = human_pitches[(-1 * notelist_size):]
    new_motif = motif_detection(pitchlist, "pitch")
    if new_motif:                                   # If motif_detection was able to find a new motif...
        motif_pool_pitches.append(new_motif)        # ...store it...
        detect_to_screen(new_motif)                 # ...and print it to the window

    durationlist = human_durations[(-1 * notelist_size):]
    new_motif = motif_detection(durationlist, "duration")
    if new_motif:                                   # If motif_detection was able to find a new motif...
        motif_pool_durations.append(new_motif)      # ...store it...
        detect_to_screen(new_motif)                 # ...and print it to the window



# ~~~~~~~~~~~~~~~~~~~~~~~Curses~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# These functions are for managing the pseudo-GUI


def info_check(some_string):
    """Send any information to a small window in the curses interface.

    This function is designed for testing. It's meant to take the place of
    the standard print function when using curses.

    Arguments:
      s(str)

    Returns:
      None
    """
    info_win.addstr("{}".format(some_string))
    info_win.refresh()


def setup_window(window, title):
    """Setup a window for later use.

    Create a window's border. Display the window's title at the top of
    the window, just underneath the border and centered. Move the cursor
    away from the title (so it isn't erased later).

    Arguments:
      window(curses window)
      title(str)

    Returns:
      None
    """
    window.border()
    height, width = window.getmaxyx()
    window.addstr(1, (width//2)-(len(title)//2), title)
    window.move(2, 1)


def motif_to_screen(motif, parameter):
    if (parameter == "pitch"):
        cur_y, cur_x = pitch_win.getyx()            # Grab the cursor's current x and y positions
        pitch_win.addstr(cur_y, cur_x, str(motif))  # Print the motif to the window
        pitch_win.move(cur_y+1, cur_x)              # Move the cursor to the next line for next time
        pitch_win.border()                          # Re-draw the border
        pitch_win.refresh()                         # Refresh the window
    if (parameter == "duration"):
        cur_y, cur_x = dur_win.getyx()         # Grab the cursor's current x and y positions
        dur_win.addstr(cur_y, cur_x, str(motif))    # Print the motif to the window
        dur_win.move(cur_y+1, cur_x)                # Move the cursor to the next line for next time
        dur_win.border()                            # Re-draw the border
        dur_win.refresh()                           # Refresh the window


def detect_to_screen(motif):
    cur_y, cur_x = dur_win.getyx()
    dur_win.addstr(cur_y, cur_x, str(motif))
    dur_win.move(cur_y+1, cur_x)
    dur_win.border()
    dur_win.refresh()


def input_to_screen(note):
    input_win.deleteln()
    input_win.insertln()
    input_win.addstr(2, 1, str(note))
    input_win.border()
    input_win.refresh()


def output_to_screen(note):
    output_win.deleteln()
    output_win.insertln()
    output_win.addstr(2, 1, note)
    output_win.border()
    output_win.refresh()


def signal_handler(signal, frame):
    """End curses and then the entire program.

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

    """
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
    stdscr.bkgd(' ', curses.color_pair(1))
    """

    # Create several subwindows to visualize data in the terminal
    input_win = stdscr.subwin(   term_height//4, term_width//4, 0,              0)
    output_win = stdscr.subwin(  term_height//4, term_width//4, term_height//4, 0)
    pitch_win = stdscr.subwin(   term_height,    term_width//4, 0,              term_width//4)
    dur_win = stdscr.subwin(     term_height,    term_width//4, 0,              term_width//2)
    info_win = stdscr.subwin(    term_height//2, term_width//4, term_height//2, 0)
    queue_win = stdscr.subwin(   term_height,    term_width//4, 0,              (term_width*3)//4)

    # Setup each window (border, title).
    setup_window(input_win, "Input")
    setup_window(output_win, "Output")
    setup_window(pitch_win, "Pitched Motifs")
    setup_window(dur_win, "Rhythmic Motifs")
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
    info_win.addstr("Ctrl-C will also end Csound.") #, curses.color_pair(1))

    # Make all the changes to curses visible.
    stdscr.refresh()

    # This section is to establish the "client" (the part of the program sending OSC data)
    output_parser = argparse.ArgumentParser()
    output_parser.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
    output_parser.add_argument("--port", type=int, default=output_OSC_port, help="The port the OSC server is listening on")
    output_args = output_parser.parse_args()
    output_client = udp_client.UDPClient(output_args.ip, output_args.port)

    input_parser = argparse.ArgumentParser()
    input_parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    input_parser.add_argument("--port", type=int, default=input_OSC_port, help="The port to listen on")
    input_args = input_parser.parse_args()

    # Dispatcher "listens" on these addresses and sends any matching information
    # to the designated function.
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/note", store_new_note)
    dispatcher.map("/motifdetection", osc_motif_detection)
    dispatcher.map("/queuenextmotif", osc_queue_next_motif)
    dispatcher.map("/generatemotif", osc_generate_motif)
    dispatcher.map("/retrievenextnote", osc_retrieve_next_note)
    dispatcher.map("/permutatemotif", osc_permutate_motif)

    # Create server.
    server = osc_server.ThreadingOSCUDPServer(
        (input_args.ip, input_args.port), dispatcher)

    # Generate a few motifs to start out.
    for i in range(randint(1, 3)):
        generate_motif("pitch")
    for i in range(randint(1, 3)):
        generate_motif("duration")

    signal.signal(signal.SIGINT, signal_handler)

    # Launch the server.
    server.serve_forever()
