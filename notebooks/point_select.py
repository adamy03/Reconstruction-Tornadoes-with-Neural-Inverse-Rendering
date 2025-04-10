import cv2
import numpy as np

# Callback function for mouse events
def select_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Point selected: ({x}, {y})")
        param.append((x, y))

def main(video_path, frame_number):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Cannot open video.")
        return

    # Read the selected frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if not ret:
        print(f"Error: Cannot read frame {frame_number}.")
        return

    # Display the frame and allow point selection
    selected_points = []
    cv2.namedWindow("Frame")
    cv2.setMouseCallback("Frame", select_point, selected_points)

    print("Click on the points you want to select. Press 'q' to quit.")
    while True:
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # Quit on 'q'
            break

    # Print selected points
    print("Selected points:", selected_points)

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_path = "/mnt/c/Users/adamf/Desktop/talbot_debris.mp4"  # Replace with your video file path
    frame_number = 12  # Replace with the frame number you want to select points on
    main(video_path, frame_number)