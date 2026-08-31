---
name: youtube-context
description: youtube, transcripts, yt-dlp, whisper, video-context
---

# YouTube Context

## Goal

Retrieve a compact, normalized transcript packet for a YouTube or other
HTTP(S) video so it can be supplied as model context.

## Input

Pass one HTTP(S) video URL to `scripts/youtube-context`.

## Output

The executable writes the packet to standard output in this exact format:

```text
Title: <title>
URL: <url>
Transcript source: <video captions or local Whisper (base.en)>

Transcript:
<normalized transcript>
```

It prefers English human or automatic captions. If the selected caption file
is missing or empty, it downloads the best audio and transcribes it locally
with Whisper. Errors go to standard error and return a non-zero status.

## Dependencies

- `yt-dlp` for metadata, captions, and audio;
- Python 3 for deterministic JSON3/WebVTT parsing and whitespace cleanup;
- `whisper` and `ffmpeg` only for the caption-free fallback.

The executable accepts configuration through `YOUTUBE_CONTEXT_*` environment
variables. The defaults match the packet consumed by the Emacs YouTube context
command.
