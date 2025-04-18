import cv2
import os

def process_videos(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4'))]
    video_files.sort()

    video_index = 0
    while 0 <= video_index < len(video_files):
        video_file = video_files[video_index]
        video_path = os.path.join(input_dir, video_file)
        print(f"Processing video: {video_file}")

        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        selected_frame = None

        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.resize(frame, (800, 600))
            display_frame = frame.copy()
            cv2.putText(display_frame, f"Frame: {frame_count + 1}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Select Frame (SPACE to select, ESC to skip, N for next, P for previous, j/k to step)", display_frame)
            
            key = cv2.waitKey(0)
            if key == ord('q'):  # quit on q
                break
            elif key == 107:  # k decrement frame idx
                frame_count = max(0, frame_count - 1)
            elif key == 106:  # j increment frame idx
                frame_count += 1
            elif key == 32:  # SPACE key to select frame
                selected_frame = frame_count + 1
                print(f"Selected frame: {selected_frame}")
                break
            elif key == ord('n'):  # 'N' key for next video
                print("Moving to next video.")
                video_index += 1
                break
            elif key == ord('p'):  # 'P' key for previous video
                print("Moving to previous video.")
                video_index -= 1
                break

            if not ret:
                print("End of video reached or error reading frame.")
                break


        if selected_frame is not None:
            output_path = os.path.join(output_dir, f"selected_{video_file}")
            save_video_from_frame(video_path, output_path, selected_frame)

        cap.release()

    cv2.destroyAllWindows()

def save_video_from_frame(input_video_path, output_video_path, start_frame):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Failed to open video for saving: {input_video_path}")
        return

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame - 1)  # Set starting frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    print(f"Saved new video to: {output_video_path}")
    cap.release()
    out.release()

if __name__ == "__main__":
    input_directory = "../data/spin_nine"
    output_directory = "../data/aligned"
    process_videos(input_directory, output_directory)