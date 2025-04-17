import argparse
import cv2
import matplotlib.pyplot as plt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--video_path")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video_path)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.resize(frame, (800, 600))
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('Frame', frame)
        key = cv2.waitKey(0) 

        if key == ord('q'):  # quit on q
            break
        elif key == 81:  # left decrement frame idx
            frame_count = max(0, frame_count - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        elif key == 83:  # right increment frame idx
            frame_count += 1

        frame_count = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

    cap.release()
    cv2.destroyAllWindows()