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

dash_input_prefix=counting-h264-vttsimple
dash_input=$dash_input_prefix.mp4

# Non-fragmented, video and text.
# It will also be our dash_input for the next steps.
cp ../counting_h264.mp4 $dash_input
MP4Box -add simple.vtt $dash_input
cp $dash_input "$DIR/out/non-frag-$dash_input"

# Fragmented, video and text.
MP4Box -dash 5000 $dash_input
dash_to_mp4_with_manifest $dash_input_prefix counting-h264-vttsimple

# Fragmented, only video.
MP4Box -dash 5000 $dash_input'#trackID=1'
dash_to_mp4_with_manifest $dash_input_prefix counting-h264

# Fragmented, only text.
MP4Box -dash 5000 $dash_input'#trackID=2'
dash_to_mp4_with_manifest $dash_input_prefix counting-vttsimple