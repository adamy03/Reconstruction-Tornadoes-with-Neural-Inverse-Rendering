#!/bin/bash
if [[ -z "$1" ]]; then
    echo "Usage: $0 <folder_of_videos>"
    exit 1
fi

cd "$1" || { echo "Failed to change directory to $1"; exit 1; }
mkdir -p aligned

for video in *.mp4; do
    if [[ -f "$video" ]]; then
        output="aligned/${video}"
        ffmpeg -i "$video" -vf "transpose=1" "$output"
    fi
done    