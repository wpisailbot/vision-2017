#Import our image processing functions to find buoys
import buoy_finder

#Import the threading library... obviously
import threading

#Import the signal handlers so that threads can be killed
import signal

#Import the class to atomically pass values
from resultpasser import ResultPasser

#Import Raspberry Pi Camera interface stuff
from picamera.array import PiRGBArray
from picamera import PiCamera

# Import OpenCV stuff for passing the processed image
import cv2

# For calculating the current frame rate, and averaging the last n
import time
import collections

# For debugging
import logging

# For sending data to the boat
import websocket

buoys_passer = ResultPasser()
heading_passer = ResultPasser()
should_run = True
logging.basicConfig(level=logging.DEBUG,
        format='[%(levelname)s] (%(threadName)s) %(message)s')

WS_SERVER = "Hercules-Linux.local"
WS_PORT = "8000"

# Calculate the mean of the values
def mean(values):
  return float(sum(values))/float(len(values))

def process_image():
  # Buffer to hold the last 10 framerates
  times = collections.deque(maxlen=10)
  last_time = 0.0
  
  # Camera Settings
  CAM_RESOLUTION = (320, 240)
  CAM_VIEW_ANGLE = (62.2, 48.8)
  camera = PiCamera()
  camera.resolution = CAM_RESOLUTION
  camera.framerate = 32
  camera.rotation = 270
  
  # Array for placing captured image
  rawCapture = PiRGBArray(camera, size=CAM_RESOLUTION)
  
  last_time = time.clock()
  count = 0
  logging.debug("Starting camera")
  # Loop the image processing
  for frame in camera.capture_continuous(rawCapture, format="bgr",
                                         use_video_port=True):
    # Loop until signaled to exit
    if not should_run:
      break

    image = frame.array
    results = buoy_finder.parse_image(image)
    # show the frame
    #cv2.imshow("Frame", image)
  
    # Causes errors if I don't do this. Yay for not understanding why...
    rawCapture.truncate(0)

    # Calculate the "heading" estimate by calculating the mean X value
    if len(results) == 0:
      heading = 0
    else: 
      heading_px = mean([x for ((x,y), rad) in results])
      # Assume that the center of the camera frame is 0 heading
      heading_px = heading_px - (CAM_RESOLUTION[0]/2.0)
      # Linearly map between pixels and angle to the camera.
      # Not "correct", but it works good enough
      heading = heading_px * float(CAM_VIEW_ANGLE[0]) / float(CAM_RESOLUTION[0])
  
    # Calculate the current framerate
    now_time = time.clock()
    times.append(1/(now_time-last_time))
    last_time = now_time
    
    # Send the timestamp and results
    buoys_passer.set((now_time, results, heading))
    # Print out the averaged framerate, number of "buoys" found, and heading estimate
    if count%100 == 0:
      logging.debug(str(sum(times)/len(times))+", "+
                    str(len(results))+", "+
                    str(heading))
    count += 10

  logging.debug("Done")

# Create JSON message for the data to send
def JSONify(buoys, heading):
  my_string = '{ "heading":%s,' % str(heading)
  my_string += '"heading_conf":%s,' % str(len(buoys))
  my_string += '"buoys":['
  for ((x,y),rad) in buoys:
    my_string += '{"x":%d,"y":%d,"radius":%d},' % (x,y,rad)
  my_string += ']}'
  return my_string

# Thread to send the current heading, and list of buoys
def send_results():
  last_timestamp = 0
  logging.debug("Starting")

  # Setup the websocket stuff
  ws = websocket.WebSocket()
  client = websocket.create_connection("ws://"+WS_SERVER+":"+WS_PORT)

  # Loop until signaled to exit
  while(should_run):
    # Get the list of buoys in the image
    value = buoys_passer.get()
    # Handle if data hasn't been set yet
    if value == None:
      continue
    # Split out the timestamp and data
    (new_timestamp, new_results, new_heading) = value
    # Only send if new data was posted
    if (new_timestamp != last_timestamp):
      last_timestamp = new_timestamp
      client.send(JSONify(new_results, new_heading))

  client.close()
  logging.debug("Done")
  return

threads = []
def kill_threads():
  print "Stopping threads"
  should_run = False
  for t in threads:
    t.join()
  print "Done"

# Enable the handler for sigint
signal.signal(signal.SIGINT, kill_threads)

# Kickoff both processes
t = threading.Thread(target=process_image, name="Image Proc")
threads.append(t)
t.start()
t = threading.Thread(target=send_results, name="Sender")
threads.append(t)
t.start()

for t in threads:
  t.join()
