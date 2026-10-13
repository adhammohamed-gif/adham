# Topic and chapter videos

The **Trim chapter videos** workflow downloads the matching original MP4 and
audio from Google Drive. It checks their alignment using waveform correlation
at three positions, then exports the 14 chapters in `chapters.json`.

The chapter boundaries were selected from the timestamped transcript, using
session introductions and closing statements. The long prayer/lunch break
and idle time between sessions are excluded. The conference ceremony is kept
as its own chapter. Internal pauses, audience questions, and panel discussions
are retained. The original recording starts during the first session.

The workflow starts automatically when its files or `chapters.json` change on
`main`. You can also open **Actions → Trim chapter videos → Run workflow**.
It exports one chapter at a time and uploads each as a separate artifact.
Download **chapter-01** through **chapter-14**, then extract the ZIPs to get
the MP4s. **chapter-index** contains the requested ranges, actual keyframe
boundaries, alignment offset, and exported durations. Download within three
days.

Video and audio streams are copied without re-encoding to preserve quality
and reduce processing time. Starts extend backward and ends extend forward
to nearby keyframes; this may include several seconds of adjacent material
and a little overlap between consecutive chapters. Check the videos before
publishing. Frame-perfect edits require re-encoding or a video editor.

If automatic alignment cannot confidently match two samples, the workflow
stops rather than using unverified timestamps. Fix the source recordings or
review the timestamp alignment before trying again.

This is a public repository. Exported recordings and workflow artifacts
should be treated as public. Artifact storage uses your GitHub Actions
allowance; this workflow does not change your billing settings.
