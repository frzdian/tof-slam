"""Task 1.1: play the RGB frames of one ZJUL5-SLAM sequence, in time order.

Usage:
    python code/task_1_1_show_rgb.py dataset/ZJUL5-SLAM/Kitchen

Keys: q = quit, space = pause/resume
"""
import glob  # find files by name pattern
import os    # work with file paths
import sys   # read arguments from the terminal

import cv2   # OpenCV: show images and draw text
import h5py  # read .h5 files (one file = one frame of data)


def timestamp_of(path):
    """Turn '.../1656938733.270982.h5' into the number 1656938733.270982."""
    filename = os.path.basename(path)     # '1656938733.270982.h5'
    without_ext = filename[:-len(".h5")]  # '1656938733.270982'
    return float(without_ext)             # sort by real time, not by text


if len(sys.argv) != 2:
    sys.exit("Usage: python code/task_1_1_show_rgb.py <sequence_folder>")
sequence = sys.argv[1]

# Every frame is one .h5 file inside the Raw folder
paths = glob.glob(os.path.join(sequence, "Raw", "*.h5"))
paths.sort(key=timestamp_of)
if not paths:
    sys.exit(f"No .h5 files found in {sequence}/Raw")
print(f"Found {len(paths)} frames")

for i, path in enumerate(paths):
    # An .h5 file works like a dictionary: ask for a key, get an array.
    # [()] means "read the whole array into memory now".
    with h5py.File(path, "r") as frame:
        rgb = frame["rgb"][()]

    if i == 0:
        height, width, channels = rgb.shape
        print(f"Width={width}, Height={height}, Channels={channels}")

    # The file stores colors as R,G,B but cv2.imshow expects B,G,R
    image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    seconds = timestamp_of(path) - timestamp_of(paths[0])
    cv2.putText(image, f"Frame {i + 1}/{len(paths)}  t={seconds:.1f}s", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow("RGB Sequence", image)

    # Wait 75 ms between frames: this dataset is about 13 frames per second
    key = cv2.waitKey(75) & 0xFF
    if key == ord("q"):
        break
    if key == ord(" "):
        cv2.waitKey(0)  # pause until any key is pressed

cv2.destroyAllWindows()
