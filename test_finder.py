import argparse
import buoy_finder
import cv2

# Parse the arguments for this program
ap = argparse.ArgumentParser()
ap.add_argument('-v', '--video', 
  help='path to the (optional) video file')
ap.add_argument('-cs', '--colorswatches',
  help='show a window with color swatches inside the HSV range')
ap.add_argument('--skip', type=int, default=0,
  help='Number of frames to skip each time')
args = vars(ap.parse_args())

cv2.namedWindow('Result', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Result', 800, 400)

# Capture video from the webcam, unless a file is specified
if not args.get("video", False):
  cap = cv2.VideoCapture(0)
else:
  cap = cv2.VideoCapture(args["video"])

while (cap.isOpened()):
  # Read in the next frame, and skip frames if desired
  for i in xrange(1+args["skip"]):
    ret, frame = cap.read()

  buoys = buoy_finder.parse_image(frame)
  print buoys

  cv2.imshow('Result', frame)

  if cv2.waitKey(1) & 0xFF == ord('q'):
    break

cap.release()
cv2.destroyAllWindows()