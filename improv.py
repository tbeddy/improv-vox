import argparse
import math

from pythonosc import dispatcher
from pythonosc import osc_server

def printCurrentNote(unused_addr, args, note):
  """
  Prints incoming notes as they are received
  """
  print("[{0}] ~ {1}".format(args[0], note))

notegroup = []
phraselist = []
def updatePhraseList(unused_addr, args, note, time):
  """
  -Receives note and time since previous note
  -Divides series of notes into phrases and appends phrases to list
  -Very crude method of dividing phrases
  """
  global notegroup
  global phraselist
  if time < 800: #800 milliseconds is an arbitrary number
    notegroup.append(note)
  else:
    print(notegroup)
    phraselist.append(notegroup)
    notegroup = []

denselist = []
def updateDensityList(unused_addr, args, density):
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
  dispatcher.map("/space", updatePhraseList, "space")
  dispatcher.map("/density", updateDensityList, "density")
  
  #Launches the server and continues to run until manually ended
  server = osc_server.ThreadingOSCUDPServer(
      (args.ip, args.port), dispatcher)
  print("Serving on {}".format(server.server_address))
  server.serve_forever()
