# Long video transcription

Transcribe a Google Drive video using free Whisper models in GitHub Actions.
The entire recording is split into 15-minute audio chunks with two seconds of
context on each side. Two chunks run at a time. The final transcript restores
timestamps to the original video; words in overlapping context are assigned
to a chunk by their midpoint to reduce duplicate text.

## Start a transcription

1. Upload your video to Google Drive. In **Share → General access**, choose
   **Anyone with the link → Viewer**. Allow viewers to download it.
2. Copy the file's sharing link, not a folder link.
3. Open this repository's **Actions → Transcribe video → Run workflow**.
4. Paste the link in **drive_url**. Choose a language (`en` for English,
   `ar` for Arabic, or `auto`) and leave the model set to `small` initially.
5. Click **Run workflow**. You can close the browser while it runs.
6. Once all jobs finish, open the run and download **transcript-and-subtitles**
   from its **Artifacts** section. Extract the ZIP on Windows.

Outputs: `transcript.txt`, `transcript.srt`, `transcript.vtt`, and
`transcript.json`. Download the final result within seven days. Intermediate
audio and text artifacts expire after one day; runs must finish within that
window. This produces a transcript, not a summary or newly written video script.
It extracts and splits audio; it does not produce trimmed video clips.

## Test first

Run a short recording first to check your language, audio quality, and Drive
download permissions. CPU transcription of ten hours can take many hours.
Accuracy varies; review names, numbers, and important passages. Splitting
reduces timeout risk but does not guarantee error-free boundary transcription.

## Cost and visibility

No paid transcription API or API key is needed. Standard GitHub-hosted runner
compute is free in public repositories. Artifact storage has separate limits;
check your GitHub Actions storage allowance before large runs. Private
repositories also have compute allowances. This project does not change
your billing settings or purchase extra capacity.

This repository is public. Treat the Drive link, workflow inputs, logs, audio
artifacts, and transcripts as public. Use a private repository for recordings
that need restricted access, subject to its Actions allowance. After processing,
you may turn off the Drive link's sharing access.

## Limits and troubleshooting

- The runner must download the video before extracting audio. Use a video
  comfortably smaller than available runner disk space (start below 8 GB).
  For very large video files, upload an audio-only version instead; MP3, M4A,
  WAV and FLAC inputs work too.
- Drive may throttle large or frequently downloaded files. A quota or access
  error requires fixing the Drive link or retrying later.
- If a chunk times out, try a smaller model. GitHub jobs have a six-hour limit.
- Up to 200 chunks are supported (about 50 hours at the default chunk length).
- For automatic language detection, each chunk detects its language separately.
  Set the language explicitly for consistent results in a single language.
- If one chunk fails, no final transcript is exported. Use **Re-run failed jobs**
  before the audio artifacts expire. Keep a local copy of the original recording.
- Speakers are not labeled. Subtitle cue length is approximate; manually review
  subtitle readability when publishing.

## Run locally

Install Python 3.11+, FFmpeg, and `pip install -r requirements.txt`.

```bash
python pipeline.py prepare "path/to/video.mp4"
python pipeline.py transcribe work/chunks/000 --model small --language en
# Repeat the transcription command for each numbered chunk folder.
python pipeline.py merge work/chunks/manifest.json work/parts
```

Dependencies: [faster-whisper](https://github.com/SYSTRAN/faster-whisper),
[gdown](https://github.com/wkentaro/gdown), and [FFmpeg](https://ffmpeg.org/).
GitHub documentation: [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
and [Actions limits](https://docs.github.com/en/actions/reference/limits).
