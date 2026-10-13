"""Download, split, transcribe and join long recordings. Python 3.11+."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
from urllib.parse import urlparse


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare(source, folder, minutes=15):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if not 1 <= minutes <= 60:
        raise ValueError("Chunk length must be 1–60 minutes")
    parsed = urlparse(source)
    if parsed.scheme == "https":
        if parsed.hostname not in {"drive.google.com", "docs.google.com"}:
            raise ValueError("Use a Google Drive file sharing link")
        import gdown
        video = folder / "source.video"
        if not gdown.download(url=source, output=str(video), fuzzy=True, quiet=True):
            raise RuntimeError("Download failed. Check Drive link access and download quota.")
    else:
        video = Path(source)
        if not video.is_file():
            raise ValueError("Source must be a local file or HTTPS Google Drive link")
    audio = folder / "audio.flac"
    run("ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", 1, "-ar", 16000, audio)
    if parsed.scheme == "https":
        video.unlink()
    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio)], text=True))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Recording has no usable audio")
    count = math.ceil(duration / (minutes * 60))
    if count > 200:
        raise ValueError("Too many chunks; use a longer chunk duration")
    chunks = []
    for i in range(count):
        start, end = i * minutes * 60, min((i + 1) * minutes * 60, duration)
        offset = max(0, start - 2)
        chunk = {"id": f"{i:03d}", "start": start, "end": end, "offset": offset}
        target = folder / chunk["id"]
        target.mkdir(exist_ok=True)
        run("ffmpeg", "-v", "error", "-y", "-ss", offset, "-i", audio,
            "-t", min(duration, end + 2) - offset, target / "audio.flac")
        write(target / "chunk.json", chunk)
        chunks.append(chunk)
    audio.unlink()
    write(folder / "manifest.json", {"duration": duration, "chunks": chunks})
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("matrix=" + json.dumps({"id": [c["id"] for c in chunks]}) + "\n")
    print(f"Prepared {len(chunks)} chunks ({duration / 3600:.2f} hours).")


def transcribe(folder, output, model, language):
    from faster_whisper import WhisperModel
    folder, output = Path(folder), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    chunk = read(folder / "chunk.json")
    engine = WhisperModel(model, device="cpu", compute_type="int8",
                          cpu_threads=os.cpu_count() or 2)
    segments, info = engine.transcribe(str(folder / "audio.flac"),
        language=None if language == "auto" else language, word_timestamps=True,
        vad_filter=True, condition_on_previous_text=False, beam_size=5)
    cues = []
    for segment in segments:
        words = []
        for word in segment.words or []:
            start, end = word.start + chunk["offset"], word.end + chunk["offset"]
            # Each word belongs to the chunk containing its midpoint.
            if chunk["start"] <= (start + end) / 2 < chunk["end"]:
                words.append({"start": max(chunk["start"], start),
                              "end": min(chunk["end"], end), "text": word.word})
        # Keep subtitle cues reasonably short, including in long segments.
        for index in range(0, len(words), 12):
            group = words[index:index + 12]
            cues.append({"start": group[0]["start"], "end": group[-1]["end"],
                         "text": "".join(w["text"] for w in group).strip()})
    write(output / f"{chunk['id']}.json", {"chunk": chunk, "language": info.language, "cues": cues})
    print(f"Finished chunk {chunk['id']}; detected language: {info.language}")


def timestamp(seconds, separator=","):
    milliseconds = max(0, round(seconds * 1000))
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    seconds, milliseconds = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}{milliseconds:03}"


def merge(manifest, parts, output):
    manifest, parts, output = read(manifest), Path(parts), Path(output)
    cues = []
    for chunk in manifest["chunks"]:
        path = parts / f"{chunk['id']}.json"
        if not path.exists():
            raise ValueError(f"Missing chunk {chunk['id']}; refusing to export an incomplete transcript")
        part = read(path)
        if part["chunk"] != chunk:
            raise ValueError("Chunk metadata differs from the recording manifest")
        cues.extend(part["cues"])
    cues.sort(key=lambda cue: cue["start"])
    output.mkdir(parents=True, exist_ok=True)
    write(output / "transcript.json", {"duration": manifest["duration"], "cues": cues})
    (output / "transcript.txt").write_text("\n".join(c["text"] for c in cues) + "\n", encoding="utf-8")
    for extension, separator in [("srt", ","), ("vtt", ".")]:
        blocks = []
        for i, cue in enumerate(cues, 1):
            blocks.append(f"{i}\n{timestamp(cue['start'], separator)} --> "
                          f"{timestamp(max(cue['end'], cue['start'] + .001), separator)}\n{cue['text']}\n")
        prefix = "WEBVTT\n\n" if extension == "vtt" else ""
        (output / f"transcript.{extension}").write_text(prefix + "\n".join(blocks), encoding="utf-8")
    print(f"Exported {len(cues)} cues from {len(manifest['chunks'])} chunks.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("source")
    prepare_parser.add_argument("--folder", default="work/chunks")
    prepare_parser.add_argument("--minutes", type=int, default=15)
    transcribe_parser = commands.add_parser("transcribe")
    transcribe_parser.add_argument("folder")
    transcribe_parser.add_argument("--output", default="work/parts")
    transcribe_parser.add_argument("--model", choices=["tiny", "base", "small", "medium"], default="small")
    transcribe_parser.add_argument("--language", default="auto")
    merge_parser = commands.add_parser("merge")
    merge_parser.add_argument("manifest")
    merge_parser.add_argument("parts")
    merge_parser.add_argument("--output", default="output")
    args = vars(parser.parse_args())
    command = args.pop("command")
    globals()[command](**args)


if __name__ == "__main__":
    main()
