"""Stage unchanged, already-exported conference MP4s for bounded file transfer."""
import hashlib
import json
from pathlib import Path

config=json.loads(Path('conference_transfer_job.json').read_text())
root=Path('work/conference-originals')
out=Path('work/conference-transfer');out.mkdir(exist_ok=True)
files=sorted(root.glob('chapter-*/*.mp4'))
assert len(files)==config['expected_videos'],f'Expected {config["expected_videos"]} videos, got {len(files)}'
manifest=[]
for video in files:
    identifier=video.parent.name.removeprefix('chapter-')
    digest=hashlib.sha256();parts=[];index=0
    with video.open('rb') as stream:
        while data:=stream.read(28*1024*1024):
            digest.update(data)
            if identifier in config.get('already_downloaded_ids',[]):continue
            index+=1
            target=out/f'{identifier}-{index:03d}.part';target.write_bytes(data)
            parts.append({'file':target.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                          'artifact_name':f'conference-transfer-{identifier}-{index:03d}'})
    manifest.append({'id':identifier,'file':video.name,'size':video.stat().st_size,
                     'sha256':digest.hexdigest(),'parts':parts,
                     'chapter':json.loads((video.parent/'chapter.json').read_text())})
(out/'manifest.json').write_text(json.dumps({'source_run':config['source_run'],'videos':manifest},indent=2))
print(f'Staged {len(manifest)} unchanged videos in {sum(len(v["parts"]) for v in manifest)} transfer parts.')
