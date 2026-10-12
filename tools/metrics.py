#!/usr/bin/env python3
"""Evaluate replay against tick-aligned ground truth. No truth => no accuracy claims.
truth JSONL: {at: seconds, entities: [{id, class, position: [x,z]}]}.
Reports explicit FP/FN counts, spatial matching, switches, and global IDF1.
"""
import argparse,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tracking.assignment import assign

def evaluate(truth,output,gate=.5):
    total_gt=total_pred=tp=fp=fn=switches=duplicates=0;errors=[];previous={};pairs={}
    for at,gt in truth.items():
        pred=output.get(at,[]);total_gt+=len(gt);total_pred+=len(pred)
        costs=np.full((len(gt),len(pred)),np.inf)
        for i,g in enumerate(gt):
            for j,p in enumerate(pred):
                if g['class']==p['category']:costs[i,j]=np.linalg.norm(np.asarray(g['position'])-p['position'])
        matches=assign(costs,gate);tp+=len(matches);fp+=len(pred)-len(matches);fn+=len(gt)-len(matches)
        used={j for _,j in matches}
        duplicates+=sum(1 for j in range(len(pred)) if j not in used and len(gt) and np.min(costs[:,j])<=gate)
        for i,j in matches:
            g,p=gt[i]['id'],pred[j]['id'];errors.append(costs[i,j]);pairs[g,p]=pairs.get((g,p),0)+1
            if g in previous and previous[g]!=p:switches+=1
            previous[g]=p
    gids=sorted({k[0] for k in pairs});pids=sorted({k[1] for k in pairs});maximum=max(pairs.values(),default=0)
    costs=np.array([[maximum-pairs.get((g,p),0) for p in pids] for g in gids])
    idtp=sum(pairs.get((gids[i],pids[j]),0) for i,j in assign(costs,maximum)) if pairs else 0
    return dict(true_positives=tp,false_positives=fp,false_negatives=fn,id_switches=switches,
                duplicate_detections=duplicates,precision=tp/max(1,tp+fp),recall=tp/max(1,tp+fn),
                idf1=2*idtp/max(1,total_gt+total_pred),mean_position_error_m=float(np.mean(errors)) if errors else None)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('truth');p.add_argument('output');p.add_argument('--gate',type=float,default=.5);a=p.parse_args()
    truth={r['at']:r['entities'] for r in map(json.loads,Path(a.truth).read_text().splitlines())}
    output={r['at']:r['unity'] for r in map(json.loads,Path(a.output).read_text().splitlines())}
    print(json.dumps(evaluate(truth,output,a.gate),indent=2))
