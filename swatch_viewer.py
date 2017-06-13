from buoy_finder import color_upper, color_lower, color2_upper, color2_lower
import cv2
import numpy as np
from math import ceil, floor

swatch_size = 5
step_size = 1
max_col = 150
h_diff = float(color_upper[0]-color_lower[0]+color2_upper[0]-color2_lower[0])
s_diff = float(color_upper[1]-color_lower[1])
v_diff = float(color_upper[2]-color_lower[2])

num_rows = ceil((ceil(h_diff/step_size)*ceil(s_diff/step_size)*ceil(v_diff/step_size/10.0))/max_col)

swatch_img = np.zeros((swatch_size*num_rows, swatch_size*max_col, 3), np.uint8)
row_num = 0
col_num = 0
for s in xrange(color_lower[1], color_upper[1], step_size):
  for v in xrange(color_lower[2], color_upper[2], step_size*10):
    for h in (range(color_lower[0], color_upper[0], step_size) +
              range(color2_lower[0], color2_upper[0], step_size)):
      cv2.rectangle(swatch_img, (swatch_size*col_num,swatch_size*row_num),
                          (swatch_size*(col_num+1), swatch_size*(row_num+1)),
                          (h,s,v), -1)

      col_num += 1
      if (col_num >= max_col):
        col_num = 0
        row_num += 1

swatch_img = cv2.cvtColor(swatch_img, cv2.COLOR_HSV2BGR)
cv2.imshow('swatches', swatch_img)

while(True):
  if cv2.waitKey(1) & 0xFF == ord('q'):
    break
