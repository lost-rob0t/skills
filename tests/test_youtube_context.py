from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/youtube-context/scripts/youtube-context"
URL = "https://www.youtube.com/watch?v=fixture"


FAKE_YT_DLP = """\
#!/usr/bin/env bash
set -euo pipefail

output=''
for ((index = 1; index <= $#; index++)); do
  if [[ "${!index}" == '--output' ]]; then
    next=$((index + 1))
    output="${!next}"
  fi
done

if [[ "$*" == *" --print "* ]]; then
  printf 'Fixture video\\n'
elif [[ "$*" == *" --format "* ]]; then
  output="${output//%(ext)s/mp3}"
  : >"$output"
elif [[ "${YOUTUBE_FIXTURE_MODE:-captions}" == 'captions' ]]; then
  output="${output//%(id)s/fixture}"
  if [[ "${YOUTUBE_FIXTURE_FORMAT:-json3}" == 'vtt' ]]; then
    output="${output//%(ext)s/vtt}"
    mkdir -p "$(dirname "$output")"
    printf '%s' $'WEBVTT\\n\\nKind: captions\\nLanguage: en\\n\\n00:00.000 --> 00:01.000\\nHello <b>world</b>\\n\\n00:01.000 --> 00:02.000\\nHello <b>world</b>\\nNext line\\n' >"$output"
  else
    output="${output//%(ext)s/json3}"
    mkdir -p "$(dirname "$output")"
    printf '%s' '{"events":[{"segs":[{"utf8":"Hello "},{"utf8":"world"}]},{"segs":[{"utf8":"Hello world"}]},{"segs":[{"utf8":"Next line"}]}]}' >"$output"
  fi
fi
"""


FAKE_WHISPER = """\
#!/usr/bin/env bash
set -euo pipefail

output_dir='.'
for ((index = 1; index <= $#; index++)); do
  if [[ "${!index}" == '--output_dir' ]]; then
    next=$((index + 1))
    output_dir="${!next}"
  fi
done
printf 'Fallback transcript' >"$output_dir/audio.txt"
"""


class YoutubeContextScriptTests(unittest.TestCase):
    def run_script(self, *, mode: str = "captions", subtitle_format: str = "json3") -> str:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            yt_dlp = bin_dir / "yt-dlp"
            yt_dlp.write_text(FAKE_YT_DLP, encoding="utf-8")
            yt_dlp.chmod(0o755)
            whisper = bin_dir / "whisper"
            whisper.write_text(FAKE_WHISPER, encoding="utf-8")
            whisper.chmod(0o755)
            ffmpeg = bin_dir / "ffmpeg"
            ffmpeg.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            ffmpeg.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["YOUTUBE_FIXTURE_MODE"] = mode
            env["YOUTUBE_FIXTURE_FORMAT"] = subtitle_format
            result = subprocess.run(
                [str(SCRIPT), URL],
                check=True,
                text=True,
                capture_output=True,
                env=env,
            )
            return result.stdout

    def test_caption_packet_is_exact_and_has_no_trailing_newline(self) -> None:
        expected = (
            "Title: Fixture video\n"
            "URL: https://www.youtube.com/watch?v=fixture\n"
            "Transcript source: video captions\n\n"
            "Transcript:\nHello world Next line"
        )
        self.assertEqual(self.run_script(), expected)
        self.assertEqual(self.run_script(subtitle_format="vtt"), expected)

    def test_whisper_fallback_uses_the_same_packet_shape(self) -> None:
        self.assertEqual(
            self.run_script(mode="fallback"),
            "Title: Fixture video\n"
            "URL: https://www.youtube.com/watch?v=fixture\n"
            "Transcript source: local Whisper (base.en)\n\n"
            "Transcript:\nFallback transcript",
        )


if __name__ == "__main__":
    unittest.main()
