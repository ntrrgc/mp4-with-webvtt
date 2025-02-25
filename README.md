Quick and dirty scripts to generate MP4 with WebVTT files.

The original video file is `LayoutTests/media/content/counting.mp4` from WebKit
(included here as `counting_mpeg4video.mp4`).

To be compatible with more browsers (namely Firefox), I recoded it to h264 with
the following command:

```
gst-launch-1.0 filesrc location=counting_mpeg4video.mp4 ! qtdemux ! decodebin ! x264enc ! mp4mux ! filesink location=counting_h264.mp4
```

`counting_h264.mp4` is used as base for the generated test vectors.

A sound track has also been added.

# How to use

Run:

```
./generate_all.sh
```

Assets are produced in the directory `out/`.

Requires Bash, MP4Box and Python3. Only tested in Linux.