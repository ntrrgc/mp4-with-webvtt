#!/bin/bash
set -eu

DIR="$(realpath "$(dirname "$0")")"
cd "$DIR"

function dash_to_mp4_with_manifest() {
    local orig_file_prefix="$1"
    shift
    local out_file_prefix="$1"
    shift

    "$DIR/mp4box_mpd_to_webkit_manifest.py" "${orig_file_prefix}_dash.mpd" \
        -u "content/${out_file_prefix}.mp4" \
        -o "$DIR/out/${out_file_prefix}-manifest.json"
    cp "${orig_file_prefix}_dashinit.mp4" "$DIR/out/${out_file_prefix}.mp4"
}

rm -rf tmp && mkdir tmp
rm -rf out && mkdir out
cd tmp

"$DIR/generate_vtt.py" > simple.vtt

# Non-fragmented, video and text
cp ../counting.mp4 counting-vttsimple.mp4
MP4Box -add simple.vtt counting-vttsimple.mp4
cp counting-vttsimple.mp4 "$DIR/out/non-frag-counting-vttsimple.mp4"

# Fragmented, video and text
MP4Box -dash 5000 'counting-vttsimple.mp4'
dash_to_mp4_with_manifest counting-vttsimple counting-video-vttsimple

# Fragmented, only video
MP4Box -dash 5000 'counting-vttsimple.mp4#trackID=1'
dash_to_mp4_with_manifest counting-vttsimple counting-video

# Fragmented, only text
MP4Box -dash 5000 'counting-vttsimple.mp4#trackID=4'
dash_to_mp4_with_manifest counting-vttsimple counting-vttsimple