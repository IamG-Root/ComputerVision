#!/usr/bin/env python3
"""Synthetic CPU benchmark; no inference, camera, broker or network measurements."""
import json
from pathlib import Path
import platform
import resource
import sys
import time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tracking.global_tracker import GlobalTracker

def run(objects,frames=40):
    tracker=GlobalTracker();times=[];cpu=time.process_time();start=time.perf_counter()
    for frame in range(frames):
        obs=[dict(key=(f'MODULE{c}','s',i),cls='person',position=[(i%10)*2+frame*.01,(i//10)*2+c*.001],confidence=.9,quality=1.,age=0.) for c in range(8) for i in range(objects)]
        t=time.perf_counter();tracker.ingest(obs,frame*.2,1700000000+frame*.2);tracker.output(frame*.2);times.append((time.perf_counter()-t)*1000)
    wall=time.perf_counter()-start
    return dict(objects=objects,cameras=8,frames=frames,mean_ms=float(np.mean(times)),p95_ms=float(np.percentile(times,95)),max_ms=max(times),cpu_seconds=time.process_time()-cpu,wall_seconds=wall,peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
if __name__=='__main__':
    print(json.dumps({'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,'kind':'synthetic development-host CPU only','results':[run(n) for n in (1,10,25)]},indent=2))
