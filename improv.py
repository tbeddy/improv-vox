import argparse
import math

from pythonosc import dispatcher
from pythonosc import osc_server

def print_note_handler(unused_addr, args, note):
  """
  Prints incoming notes as they are received
  """
  print("[{0}] ~ {1}".format(args[0], note))

def print_compute_handler(unused_addr, args, volume):
  try:
    print("[{0}] ~ {1}".format(args[0], args[1](volume)))
  except ValueError: pass

notegroup = []
phraselist = []
def lol(unused_addr, args, note, time):
  global notegroup
  if time < 800:
    notegroup.append(note)
  else:
    print(notegroup)
    notegroup = []

denselist = []
def makeDensityList(unused_addr, args, density):
  """
  -Receives the note density at a regular interval of time
  -Appends the value to a global list variable
  -Interval is set in Max/MSP
  """
  global denselist
  denselist.append(density)
    
if __name__ == "__main__":    
  parser = argparse.ArgumentParser()
  parser.add_argument("--ip",
      default="127.0.0.1", help="The ip to listen on")
  parser.add_argument("--port",
      type=int, default=5005, help="The port to listen on")
  args = parser.parse_args()

  #Dispatcher "listens" on these addresses and sends any matching information
  #to the designated function
  dispatcher = dispatcher.Dispatcher()
  dispatcher.map("/debug", print)
  dispatcher.map("/space", lol, "space")
  dispatcher.map("/density", makeDensityList, "space")
  dispatcher.map("/logvolume", print_compute_handler, "Log volume", math.log)

  #Launches the server and continues to run until manually ended
  server = osc_server.ThreadingOSCUDPServer(
      (args.ip, args.port), dispatcher)
  print("Serving on {}".format(server.server_address))
  server.serve_forever()
