#!/bin/bash
if [[ -z "$1" ]]; then
    echo "Usage: $0 <folder_of_videos>"
    exit 1
fi

cd "$1" || { echo "Failed to change directory to $1"; exit 1; }
mkdir -p frames

for video in *.mp4; do
    if [[ -f "$video" ]]; then
        output="frames/${video%.*}_frame1.jpg"
        ffmpeg -i "$video" -ss 00:00:00 -frames:v 1 -q:v 3 "$output"
        echo "Extracted first frame from $video to $output"
    fi
done    