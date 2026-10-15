"""Inspect a lecture, then export reviewed topic clips no longer than five minutes."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

MAX_SECONDS = 299.5  # Allow for AAC padding while keeping the MP4 under 300 seconds.


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)], text=True))


def download(config):
    import gdown
    source=Path('work/source.mp4');source.parent.mkdir(exist_ok=True)
    url=config['source_url']
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in {'drive.google.com','docs.google.com'}:
        raise ValueError('Use an HTTPS Google Drive file link')
    if not source.exists():
        if not gdown.download(url=url,output=str(source),fuzzy=True,quiet=True):
            raise RuntimeError('Drive download failed; check sharing and download quota')
    data=probe(source)
    if not any(s['codec_type']=='video' for s in data['streams']):
        raise ValueError('Input does not contain a video stream')
    return source,data


def stamp(value, separator=','):
    ms=max(0,round(value*1000));hours,left=divmod(ms,3600000);minutes,left=divmod(left,60000);seconds,ms=divmod(left,1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{separator}{ms:03}'


def inspect(config):
    from faster_whisper import WhisperModel
    source,metadata=download(config)
    out=Path('work/analysis');out.mkdir(exist_ok=True)
    duration=float(metadata['format']['duration'])
    write(out/'metadata.json',{'duration':duration,'streams':metadata['streams']})
    audio=Path('work/audio.flac')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-vn','-ac','1','-ar','16000',str(audio)],check=True)
    import os
    engine=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=os.cpu_count() or 2)
    segments,info=engine.transcribe(str(audio),word_timestamps=True,vad_filter=True,condition_on_previous_text=False,beam_size=5)
    cues=[]
    for segment in segments:
        cue={'start':round(segment.start,3),'end':round(segment.end,3),'text':segment.text.strip(),
             'words':[{'start':round(w.start,3),'end':round(w.end,3),'text':w.word} for w in segment.words or []]}
        cues.append(cue)
        if len(cues)%50==0:print(f'Transcribed through {stamp(segment.end)}',flush=True)
    write(out/'transcript.json',{'duration':duration,'language':info.language,'cues':cues})
    (out/'transcript.txt').write_text('\n'.join(f"[{stamp(c['start'],'.')}] {c['text']}" for c in cues),encoding='utf-8')
    (out/'transcript.srt').write_text('\n'.join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}\n" for i,c in enumerate(cues,1)),encoding='utf-8')
    frames=out/'frames';frames.mkdir(exist_ok=True)
    for seconds in sorted(set([min(30,duration/2)]+list(range(300,int(duration),300)))):
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(source),'-frames:v','1','-vf','scale=960:-2','-q:v','3',str(frames/f'{int(seconds):05d}.jpg')],check=True)
    print(f'Analysis ready: {duration/60:.1f} minutes; language {info.language}; {len(cues)} cues',flush=True)


def validate_clips(config, duration):
    seen=set()
    if not config.get('clips'):
        raise ValueError('No reviewed clip ranges have been supplied')
    for clip in config['clips']:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',clip['id']) or clip['id'] in seen:
            raise ValueError('Clip identifiers must be unique and filename-safe')
        seen.add(clip['id'])
        start,end=clip['start'],clip['end']
        if not all(isinstance(t,(int,float)) and math.isfinite(t) for t in [start,end]):
            raise ValueError('Timestamps must be finite numbers')
        if not 0<=start<end<=duration+.05 or end-start>MAX_SECONDS:
            raise ValueError(f"Invalid range or clip over five minutes: {clip['id']}")
        if not clip.get('title','').strip():
            raise ValueError('Each clip needs an informative title')


def prepare(config):
    source,metadata=download(config)
    validate_clips(config,float(metadata['format']['duration']))
    Path('work/exports').mkdir(exist_ok=True)
    Path('work/reports').mkdir(exist_ok=True)
    print(f"Prepared {len(config['clips'])} topic clips; maximum requested duration {max(c['end']-c['start'] for c in config['clips']):.2f}s")


def cut(config, identifier):
    source=Path('work/source.mp4')
    validate_clips(config,float(probe(source)['format']['duration']))
    clip=next(c for c in config['clips'] if c['id']==identifier)
    duration=clip['end']-clip['start']
    folder=Path('work/exports')/clip['id'];folder.mkdir(parents=True,exist_ok=True)
    slug=re.sub(r'[^\w-]+','-',clip['title'],flags=re.UNICODE).strip('-')[:90]
    output=folder/f"{clip['id']}-{slug}.mp4"
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(clip['start']),'-i',str(source),'-t',f'{duration:.3f}',
        '-map','0:v:0','-map','0:a:0?','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2',
        '-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',
        '-movflags','+faststart',str(output)],check=True)
    info=probe(output);actual=float(info['format']['duration'])
    if actual>300 or actual<max(0,duration-1):
        raise ValueError(f'Export duration check failed: {actual}s')
    report={**clip,'output_file':output.name,'actual_duration':actual,'size_bytes':output.stat().st_size}
    write(folder/'clip.json',report);write(Path('work/reports')/f"{clip['id']}.json",report)
    print(f"Exported {clip['id']}: {clip['title']} ({actual:.2f}s)",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect','prepare','cut'])
    parser.add_argument('--config',default='short_clips_job.json')
    parser.add_argument('--id')
    args=parser.parse_args();config=json.loads(Path(args.config).read_text(encoding='utf-8'))
    if args.command=='cut':
        if not args.id:parser.error('cut requires --id')
        cut(config,args.id)
    else:globals()[args.command](config)


if __name__=='__main__':main()
