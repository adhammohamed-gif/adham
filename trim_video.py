"""Export transcript-selected chapters after checking audio/video alignment."""
import argparse
import csv
import json
from pathlib import Path
import re
import subprocess


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path)], text=True))


def validate(config):
    chapters = config["chapters"]
    if not chapters or len(chapters) > 100:
        raise ValueError("Supply 1–100 chapters")
    previous = 0
    identifiers = set()
    for chapter in chapters:
        if chapter["id"] in identifiers or not re.fullmatch(r"[A-Za-z0-9_-]+", chapter["id"]):
            raise ValueError("Chapter IDs must be unique and filename-safe")
        identifiers.add(chapter["id"])
        start, end = chapter["start"], chapter["end"]
        if not 0 <= start < end <= config["transcript_duration"] or start < previous:
            raise ValueError("Chapter ranges must be ordered, non-overlapping and within the transcript")
        previous = end


def samples(path, start, length):
    import numpy as np
    data = subprocess.check_output([
        "ffmpeg", "-v", "error", "-ss", str(start), "-i", str(path),
        "-t", str(length), "-vn", "-ac", "1", "-ar", "8000",
        "-f", "f32le", "pipe:1"])
    return np.frombuffer(data, dtype="<f4").astype(np.float64)


def alignment(video, audio, duration):
    import numpy as np
    from scipy.signal import correlate
    offsets = []
    for position in [duration * .02, duration * .60, duration * .90]:
        reference = samples(audio, position, 20)
        base = max(0, position - 30)
        candidate = samples(video, base, 80)
        reference = reference - reference.mean()
        if np.linalg.norm(reference) < .01 or len(candidate) < len(reference):
            continue
        candidate = candidate - candidate.mean()
        correlation = correlate(candidate, reference, mode="valid", method="fft")
        energy = np.concatenate(([0], np.cumsum(candidate * candidate)))
        energy = energy[len(reference):] - energy[:-len(reference)]
        score = correlation / np.maximum(np.sqrt(np.maximum(energy, 0)) * np.linalg.norm(reference), 1e-12)
        best = int(np.argmax(score))
        confidence = float(score[best])
        offset = base + best / 8000 - position
        print(f"Alignment check at {position:.0f}s: offset={offset:.3f}s, match={confidence:.3f}")
        if confidence >= .4:
            offsets.append(offset)
    if len(offsets) < 2 or max(offsets) - min(offsets) > .5:
        raise ValueError("Audio/video alignment could not be verified consistently; review timestamps manually")
    return float(np.median(offsets))


def download(url, target):
    import gdown
    if not gdown.download(url=url, output=str(target), fuzzy=True, quiet=True):
        raise RuntimeError("Drive download failed; check download access or quota")


def prepare(config_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    validate(config)
    folder = Path("work/trim")
    folder.mkdir(parents=True, exist_ok=True)
    video, audio = folder / "source.mp4", folder / "reference.m4a"
    download(config["video_url"], video)
    download(config["reference_audio_url"], audio)
    metadata = probe(video)
    if not any(stream["codec_type"] == "video" for stream in metadata["streams"]):
        raise ValueError("The source file has no video stream")
    duration = float(metadata["format"]["duration"])
    offset = alignment(video, audio, config["transcript_duration"])
    if abs(duration - (config["transcript_duration"] + offset)) > 5:
        raise ValueError("Video and transcript duration differ by more than five seconds")
    audio.unlink()
    Path("work/trim/alignment.json").write_text(json.dumps({"offset": offset, "duration": duration}))
    print(f"Verified recording alignment. Video duration {duration:.3f}s; offset {offset:.3f}s")


def boundary(video, target, duration, before):
    frames = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey",
        "-read_intervals", f"{max(0, target - 30)}%+65", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(video)], text=True))["frames"]
    times = [float(frame["best_effort_timestamp_time"]) for frame in frames
             if "best_effort_timestamp_time" in frame]
    candidates = [value for value in times if (value <= target if before else value >= target)]
    if before:
        actual = max(candidates, default=0 if target < 30 else target)
    else:
        actual = min(candidates, default=min(target, duration))
    if abs(actual - target) > 30:
        raise ValueError("Keyframes are too far apart for clean chapter cuts")
    return max(0, min(actual, duration))


def cut(config_path, identifier):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    validate(config)
    chapter = next(item for item in config["chapters"] if item["id"] == identifier)
    state = json.loads(Path("work/trim/alignment.json").read_text())
    video = Path("work/trim/source.mp4")
    start = max(0, chapter["start"] + state["offset"])
    end = min(state["duration"], chapter["end"] + state["offset"])
    start = boundary(video, start, state["duration"], True)
    end = boundary(video, end, state["duration"], False)
    if end <= start:
        raise ValueError("Adjusted chapter range is empty")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", chapter["title"]).strip("-")[:110]
    folder = Path("work/trim/exports") / identifier
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / f"{identifier}-{slug}.mp4"
    run("ffmpeg", "-v", "error", "-y", "-ss", start, "-i", video,
        "-t", end - start, "-map", "0:v:0", "-map", "0:a:0", "-c", "copy",
        "-avoid_negative_ts", "make_zero", "-movflags", "+faststart", output)
    result = {**chapter, "video_start": start, "video_end": end,
              "output_duration": float(probe(output)["format"]["duration"]), "file": output.name}
    if result["output_duration"] < (end - start) - 5:
        raise ValueError("Exported chapter is unexpectedly short")
    (folder / "chapter.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    reports = Path("work/trim/reports")
    reports.mkdir(exist_ok=True)
    (reports / f"{identifier}.json").write_text(json.dumps(result), encoding="utf-8")
    print(f"Exported chapter {identifier}: {chapter['title']} ({result['output_duration'] / 60:.1f} minutes)")


def report():
    folder = Path("work/trim/reports")
    rows = [json.loads(p.read_text()) for p in sorted(folder.glob("*.json"))]
    with (folder / "chapters.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote report for {len(rows)} chapters")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "cut", "report"])
    parser.add_argument("--config", default="chapters.json")
    parser.add_argument("--id")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.config)
    elif args.command == "cut":
        if not args.id:
            parser.error("cut requires --id")
        cut(args.config, args.id)
    else:
        report()
