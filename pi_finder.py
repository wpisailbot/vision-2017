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

buoys_passer = ResultPasser()
heading_passer = ResultPasser()
should_run = True
logging.basicConfig(level=logging.DEBUG,
        format='[%(levelname)s] (%(threadName)s) %(message)s')

def process_image():
  # Buffer to hold the last 10 framerates
  times = collections.deque(maxlen=10)
  last_time = 0.0
  
  # Camera Settings
  CAM_RESOLUTION = (320, 240)
  camera = PiCamera()
  camera.resolution = CAM_RESOLUTION
  camera.framerate = 32
  
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
  
    # Calculate the current framerate
    now_time = time.clock()
    times.append(1/(now_time-last_time))
    last_time = now_time
    
    # Send the timestamp and results
    buoys_passer.set((now_time, results))
    # Print out the averaged framerate, and number of "buoys" found
    if count%100 == 0:
      logging.debug(str(sum(times)/len(times))+", "+str(len(results)))
    count += 10

  logging.debug("Done")

def send_results():
  last_timestamp = 0

  logging.debug("Starting")
  # Loop until signaled to exit
  while(should_run):
    
    value = buoys_passer.get()
    if value == None:
      continue
    (new_timestamp, new_results) = value
    if (new_timestamp != last_timestamp):
      logging.debug(new_timestamp)
      last_timestamp = new_timestamp
  
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