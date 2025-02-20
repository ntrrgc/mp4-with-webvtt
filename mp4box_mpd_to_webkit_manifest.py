#!/usr/bin/env python3
"""
https://gist.github.com/ntrrgc/f00c31e284663fd85e0b2b2a64f68ceb
mp4box_mpd_to_webkit_manifest.py:

Small utility to convert a DASH MPD file coming from MP4Box into a much simpler
JSON manifest as used in WebKit LayoutTests.

---

MIT License

Copyright (c) 2025 Alicia Boya García

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations
import io
import json
from pathlib import Path
import re
import sys
import argparse
from typing import Any, TextIO, TypedDict
from lxml import etree


class WebKitManifest(TypedDict):
    url: str
    type: str
    init: WebKitManifestInit
    duration: float
    media: list[WebKitManifestMedia]
class WebKitManifestInit(TypedDict):
    offset: int
    size: int
class WebKitManifestMedia(TypedDict):
    offset: int
    size: int
    timestamp: float
    duration: float


def open_or_stdout(path: str) -> TextIO:
    if path == "--":
        return sys.stdout
    return open(path, "w")

def prettyprint(element, **kwargs):
    xml = etree.tostring(element, pretty_print=True, **kwargs) # type: ignore
    print(xml.decode(), end='')

def period_dur_to_secs(period_dur: str) -> float:
    match = re.match(r"PT(\d+)H(\d+)M(\d+\.\d+)S", period_dur)
    assert match
    str_hours, str_min, str_seconds = match.groups()
    return float(str_seconds) + 60 * int(str_min) + 3600 * int(str_hours)

def range_str_to_ints(text: str) -> tuple[int, int]:
    a, b = text.split("-")
    return int(a), int(b)

NSMAP = {"m": "urn:mpeg:dash:schema:mpd:2011"}

def xpath(doc, expr: str) -> list[Any]:
    return doc.xpath(expr, namespaces=NSMAP)

def xpath_single(doc, expr: str):
    results = xpath(doc, expr)
    assert len(results) == 1, f"XPath {expr!r} should have returned 1 result, got {len(results)}"
    return results[0]

def size_from_inclusive_range(start: int, end: int) -> int:
    return end - start + 1

def _mpd_to_webkit(doc, content_url: str) -> WebKitManifest:
    # Assume only one period
    mime_type = xpath_single(doc, "//m:Representation/@mimeType")
    codecs = xpath_single(doc, "//m:Representation/@codecs")
    total_dur = period_dur_to_secs(xpath_single(doc, "/m:MPD/m:Period/@duration"))
    timescale = int(xpath_single(doc, "//m:SegmentList/@timescale"))
    seg_dur_in_timescale = int(xpath_single(doc, "//m:SegmentList/@duration"))
    init_range = range_str_to_ints(xpath_single(doc, "//m:Initialization/@range"))
    segment_byte_ranges = list(map(range_str_to_ints, xpath(doc, "//m:SegmentURL/@mediaRange")))
    return {
        "url": content_url,
        "type": f'{mime_type}; codecs="{codecs}"',
        "init": {
            "offset": init_range[0],
            "size": size_from_inclusive_range(*init_range),
        },
        "duration": total_dur,
        "media": [
            {
                "offset": byte_range[0],
                "size": size_from_inclusive_range(*byte_range),
                "timestamp": i * seg_dur_in_timescale / timescale,
                "duration": min(total_dur, (i + 1) * seg_dur_in_timescale / timescale)
            }
            for i, byte_range in enumerate(segment_byte_ranges)
        ]
    }

def pretty_one_liner_dict(data: dict[Any, Any]) -> str:
    # This just happens to be a style favored in other manifests and in WebKit
    # code in general:
    # { "offset": 1270, "size": 1270 }
    ret = json.dumps(data)
    assert ret[0] == "{" and ret[-1] == "}"
    return f"{{ {ret[1:-1]} }}"

def compact_json_dump(data: Any, indent: str, _cur_indent_level: int = 0) -> str:
    if isinstance(data, dict) and "offset" in data:
        return pretty_one_liner_dict(data)
    if not isinstance(data, dict) and not isinstance(data, list):
        return json.dumps(data)
    if isinstance(data, list):
        char_start, char_end, items = "[", "]", data
    else:
        char_start, char_end, items = "{", "}", data.items()
    buf = io.StringIO()
    buf.write(char_start)
    item_prefix = indent * (_cur_indent_level + 1)
    is_first = True
    for item in items:
        buf.write("\n" if is_first else ",\n")
        buf.write(item_prefix)
        if isinstance(data, dict):
            key, val = item
            buf.write(json.dumps(key) + ': ')
        else:
            val = item
        buf.write(compact_json_dump(val, indent, _cur_indent_level + 1))
        is_first = False
    buf.write("\n")
    buf.write(indent * _cur_indent_level)
    buf.write(char_end)
    return buf.getvalue()

def mpd_to_webkit(mpd_path: str, manifest_path: str, content_url: str):
    with open_or_stdout(manifest_path) as fo:
        doc = etree.parse(mpd_path) # type: ignore
        manifest = _mpd_to_webkit(doc, content_url)
        fo.write(compact_json_dump(manifest, indent=" " * 4))

def main():
    parser = argparse.ArgumentParser(sys.argv[0], description="""
Given an MPD file generated by MP4Box, generate a WebKit manifest like the ones
in LayoutTests/media/media-source/content/*.json.

Note this tool does in no way attempt to comply with the entire MPD
specification. Its goal is to handle just enough to produce test vectors for
MediaSource Extensions.
""")
    parser.add_argument("mpd_file", type=str,
        help="An .mpd file produced by MP4Box describing several media segments"
        " in the same file")
    parser.add_argument("-u", "--url",
        help="What to put in the \"url\" field of the manifest", required=True)
    parser.add_argument("-o", "--output", default="--",
        help="Where to write the WebKit manifest to")

    args = parser.parse_args()
    mpd_to_webkit(args.mpd_file, args.output, args.url)

if __name__ == "__main__":
    main()