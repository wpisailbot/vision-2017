import numpy as np
import cv2

# HSV thresholds (red wraps around from 179 to 0)
color_lower = np.array([174,140,0])
color_upper = np.array([180,255,255])
color2_lower = np.array([0,140,0])
color2_upper = np.array([10,255,255])

# Kernel size for erode and dilate
kernel = np.ones((5,5), np.uint8)

def parse_image(image_frame):
  # Convert to HSV color space
  hsv_frame = cv2.cvtColor(image_frame, cv2.COLOR_BGR2HSV)
  # Split out the HSV values
  hue, sat, val = cv2.split(hsv_frame)
  
  # Mask off the desired color in the HSV color space
  hsv_mask = cv2.inRange(hsv_frame, color_lower, color_upper)
  hsv2_mask = cv2.inRange(hsv_frame, color2_lower, color2_upper)
  # Combine the two masks b/c red wraps around from 255 to 0
  hsv_mask = cv2.add(hsv_mask, hsv2_mask)

  #Erode and Dilate to get rid of image noise
  hsv_mask_filt = cv2.erode(hsv_mask, kernel, iterations=1)
  hsv_mask_filt = cv2.dilate(hsv_mask_filt, kernel, iterations=1)

  # Find contours in the masked image to find possible buoy locations
  contours = cv2.findContours(hsv_mask_filt.copy(), cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_SIMPLE)[-2]
  # Only search if there are contours available
  buoys = []
  if len(contours) > 0:
    # find the largest contour, and compute its minimum enclosing circle, and centroid
    for c in contours:
      ((x_loc,y_loc), radius) = cv2.minEnclosingCircle(c)
      M = cv2.moments(c)
      #center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
      # draw a circle on the largest thing it found
      #cv2.circle(image_frame, (int(x_loc),int(y_loc)), int(radius), (0,0,255), 2) 
      buoys.append(((x_loc,y_loc),radius))
  return buoys
