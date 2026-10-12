#!/usr/bin/env python3
"""Offline replay. Each JSONL line: at (relative seconds), module, payload.
Optional truth is a list of {id, class, position} for that evaluation tick.
Same input can be used with --engine baseline and --engine new.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input');ap.add_argument('--engine',choices=['new','baseline'],default='new')
    ap.add_argument('--output',required=True);ap.add_argument('--tail',type=float,default=6)
    args=ap.parse_args()
    sys.path.insert(0,str(ROOT/('server' if args.engine=='new' else 'tests/baseline')))
    from processing import DataProcessing
    events=[json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    events.sort(key=lambda e:e['at'])
    now=[0.];epoch=1700000000.
    if args.engine=='new':p=DataProcessing(clock=lambda:now[0],wall=lambda:epoch+now[0])
    else:
        import processing
        processing.time.time=lambda:epoch+now[0]
        p=DataProcessing()
    index=0;records=[];tick=0
    end=(events[-1]['at'] if events else 0)+args.tail
    while tick*.2<=end:
        now[0]=round(tick*.2,6)
        while index<len(events) and events[index]['at']<=now[0]:
            e=events[index];payload=e['payload']
            if args.engine=='baseline' and isinstance(payload,dict):
                payload=[{'id':o['local_track_id'],'class':o['class'],'position':o['position']} for o in payload['entities'] if o.get('track_state','observed')=='observed']
            msg=types.SimpleNamespace(topic='CV/'+e['module'],payload=json.dumps(payload).encode(),retain=False)
            p.on_message(None,None,msg);index+=1
        start=time.perf_counter();result=p.compute(tick);elapsed=time.perf_counter()-start
        entities=[o for group in result.values() for o in group]
        records.append({'at':now[0],'unity':p.format_array_for_unity(entities),'processing_ms':elapsed*1000})
        tick+=1
    Path(args.output).write_text(''.join(json.dumps(r)+'\n' for r in records))
    print(json.dumps({'engine':args.engine,'ticks':len(records),'max_entities':max((len(r['unity']) for r in records),default=0),'last_nonempty':max((r['at'] for r in records if r['unity']),default=None)}))

if __name__=='__main__':main()
