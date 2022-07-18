import cv2
import numpy as np

def get_background(file_path):
    cap = cv2.VideoCapture(file_path)
    # we will randomly select 50 frames for the calculating the median
    frame_indices = cap.get(cv2.CAP_PROP_FRAME_COUNT) * np.random.uniform(size=50)

    # we will store the frames in array
    frames = []
    for idx in frame_indices:
        # set the frame id to read that particular frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        frames.append(frame)

    # calculate the median
    median_frame = np.median(frames, axis=0).astype(np.uint8)

    return median_frame


cap = cv2.VideoCapture('river3.mp4')

cv2.namedWindow("Frame")

# get the video frame height and width
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

# get the background model
background = get_background('river3.mp4')
# convert the background model to grayscale format
background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
frame_count = 0
consecutive_frame = 8

points_of_interest = []

while (cap.isOpened()):
    ret, frame = cap.read()
    if ret == True:
        frame_count += 1
        orig_frame = frame.copy()
        # IMPORTANT STEP: convert the frame to grayscale first
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if frame_count % consecutive_frame == 0 or frame_count == 1:
            frame_diff_list = []
        # find the difference between current frame and base frame
        frame_diff = cv2.absdiff(gray, background)
        # thresholding to convert the frame to binary
        ret, thres = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)
        # dilate the frame a bit to get some more white area...
        # ... makes the detection of contours a bit easier
        dilate_frame = cv2.dilate(thres, None, iterations=2)
        # append the final result into the `frame_diff_list`
        frame_diff_list.append(dilate_frame)
        # if we have reached `consecutive_frame` number of frames
        if len(frame_diff_list) == consecutive_frame:
            # add all the frames in the `frame_diff_list`
            sum_frames = sum(frame_diff_list)
            # find the contours around the white segmented areas
            contours, hierarchy = cv2.findContours(sum_frames, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # draw the contours, not strictly necessary
            for i, cnt in enumerate(contours):
                cv2.drawContours(frame, contours, i, (0, 0, 255), 3)
            for contour in contours:
                # continue through the loop if contour area is less than 500...
                # ... helps in removing noise detection
                if cv2.contourArea(contour) < 100:
                    continue
                if cv2.contourArea(contour) > 400:
                  continue
                # get the xmin, ymin, width, and height coordinates from the contours
                (x, y, w, h) = cv2.boundingRect(contour)

                points_of_interest.append((x, y))
                # draw the bounding boxes
                cv2.rectangle(orig_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.imshow('Frame', orig_frame)
            cv2.waitKey(1000)
            break
            # # out.write(orig_frame)
            # if cv2.waitKey(100) & 0xFF == ord('q'):
            #     break
    else:
        break

cap.release()

cap = cv2.VideoCapture('river3.mp4')

avg_speed = None

# Perform optical flow on points of interest.
for index, point in enumerate(points_of_interest):

  ret, frame = cap.read()

  # Create old frame
  old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

  lk_params = dict(winSize = (10, 10),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

  i_x, i_y = point

  old_points = np.array([[i_x, i_y]], dtype=np.float32)

  speed = 0
  mpi = 0.001
  count = 0
  time = 0

  while True and cap.isOpened():
    ret, frame = cap.read()
    if not ret:
      break

    count = count + 1

    if count == 5:
      count = 0
    else:
      key = cv2.waitKey(33)
      continue

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.circle(frame, point, 5, (0, 0, 255))

    new_points, status, error = cv2.calcOpticalFlowPyrLK(
      old_gray, gray_frame, old_points, None, **lk_params)
    old_gray = gray_frame.copy()
    old_points = new_points
    x, y = new_points.ravel()
    if x < 0 or y < 0 or x > frame.shape[1] or y > frame.shape[0]:
      break

    distance = ((x - i_x) * (x - i_x)) + ((y - i_y) * (y - i_y))
    distance_km = distance * 0.001 * mpi
    time_s = time * 0.001
    time_m = time_s / 60
    time_hr = time_m / 60
    speed = distance_km / time_hr


    cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0))

    cv2.imshow("Frame", frame)

    key = cv2.waitKey(33)
    time = time + 33
    if key == 27:
      break

  if index == 0:
    avg_speed = speed
  else:
    avg_speed = ((avg_speed * i) + speed) / (i + 1)

  cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

  print(avg_speed)

cap.release()
cv2.destroyAllWindows()
