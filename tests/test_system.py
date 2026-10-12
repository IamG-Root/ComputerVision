import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'server'))
import config as cfg
from processing import DataProcessing
from tracking.assignment import assign
from tracking.global_tracker import GlobalTracker, Policy
from tracking.local_tracker import LocalTracker
from tracking.protocol import decode
from tracking.visibility import quality, footprint


def observation(camera='MODULE1', ident=1, x=1., z=1., cls='person'):
    return dict(key=(camera,'s',ident),cls=cls,position=[x,z],confidence=.9,quality=1.,age=0.)

def packet(frame=0, module='MODULE1', entities=None, session='s', capture=100.):
    return dict(version=2,module_id=module,session_id=session,frame_id=frame,capture_timestamp=capture,
        clock_synchronized=False,entities=entities if entities is not None else
        [dict(local_track_id=1, **{'class':'person'},position=[1.,1.],confidence=.9,track_state='observed',observation_age=0.)])

def message(data, module='MODULE1', retain=False):
    return types.SimpleNamespace(topic='CV/'+module,payload=json.dumps(data).encode(),retain=retain)

class Contract(unittest.TestCase):
    def test_exact_fixtures(self):
        os.environ['TZ']='UTC';time.tzset()
        f=json.loads((ROOT/'tests/fixtures/contract.json').read_text())
        self.assertEqual(f['topics'],[cfg.LOCAL_PUB_TOPIC,cfg.FIWARE_PUB_TOPIC])
        for case in f['cases']:
            self.assertEqual(json.dumps(DataProcessing.format_array_for_unity(case['input'])),json.dumps(case['unity']))
            self.assertEqual(json.dumps(DataProcessing.format_array_for_fiware(case['input'])),json.dumps(case['fiware']))

    def test_serializers_ast_unchanged(self):
        def methods(path):
            tree=ast.parse(path.read_text())
            return {n.name:ast.dump(n) for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('format_array')}
        self.assertEqual(methods(ROOT/'server/legacy_output.py'),methods(ROOT/'tests/baseline/processing.py'))

    def test_publisher_cardinality_unchanged(self):
        def publication(path):
            tree=ast.parse(path.read_text())
            return [ast.dump(n) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='send']
        self.assertEqual(publication(ROOT/'server/main.py'),publication(ROOT/'tests/baseline/main.py'))
        # Execute actual publication slice with empty and multiple entity inputs.
        text=(ROOT/'server/main.py').read_text()
        part=text[text.index('                entities_array = []'):text.index('            time.sleep')]
        import textwrap
        for entities in ({}, {'person':[{'id':1,'class':'person','position':[1.,2.],'last_update':100}, {'id':2,'class':'person','position':[2.,3.],'last_update':100}]}):
            local,fiware=MagicMock(),MagicMock()
            exec(textwrap.dedent(part),dict(entities=entities,processor=DataProcessing(),local_conn=local,fiware_conn=fiware,json=json))
            self.assertEqual(local.send.call_count,1)
            self.assertEqual(fiware.send.call_count,sum(map(len,entities.values())))

class Assignment(unittest.TestCase):
    def test_gating_before_optimization(self):
        self.assertEqual(assign([[.1,100],[100,.2]],1),[(0,0),(1,1)])
    def test_unmatched(self):
        self.assertEqual(assign([[100],[.1],[100]],1),[(1,0)])
    def test_empty(self):
        self.assertEqual(assign(np.empty((0,3)),1),[])
    def test_invalid(self):
        self.assertEqual(assign([[np.nan,np.inf]],1),[])

class Global(unittest.TestCase):
    def run_frames(self, cameras=1, objects=1, reverse=False):
        tracker=GlobalTracker()
        for frame in range(5):
            rows=[observation(f'MODULE{c}',i,x=i*2.+frame*.08+c*.002) for c in range(cameras) for i in range(objects)]
            tracker.ingest(rows[::-1] if reverse else rows,frame*.2,100+frame*.2)
        return tracker
    def test_one_camera(self): self.assertEqual(len(self.run_frames().output(.8)['person']),1)
    def test_two_cameras(self): self.assertEqual(len(self.run_frames(2).output(.8)['person']),1)
    def test_three_cameras(self): self.assertEqual(len(self.run_frames(3).output(.8)['person']),1)
    def test_eight_cameras(self): self.assertEqual(len(self.run_frames(8).output(.8)['person']),1)
    def test_multiple_objects(self): self.assertEqual(len(self.run_frames(8,3).output(.8)['person']),3)
    def test_permutation(self): self.assertEqual(self.run_frames(8,3).output(.8),self.run_frames(8,3,True).output(.8))
    def test_lifecycle(self):
        t=self.run_frames();self.assertEqual(t.output(.8)['person'][0]['id'],1)
        self.assertFalse(t.output(1.5));self.assertEqual(t.tracks[1].state,'Occluded')
        t.output(2.4);self.assertEqual(t.tracks[1].state,'Lost')
        t.output(5.);self.assertFalse(t.tracks)
    def test_occlusion_return(self):
        t=self.run_frames();t.output(1.5);t.ingest([observation(x=.5)],1.6,101.6)
        self.assertEqual(t.output(1.6)['person'][0]['id'],1)
    def test_handoff(self):
        t=self.run_frames();t.ingest([observation('MODULE9',20,x=.4)],1.,101.)
        self.assertEqual(t.output(1.)['person'][0]['id'],1)
    def test_different_classes(self):
        t=GlobalTracker(Policy(confirm_hits=1));t.ingest([observation(),observation('MODULE2',cls='pallet')],0,100)
        self.assertEqual(len(t.tracks),2)
    def test_same_camera_constraint(self):
        t=GlobalTracker();t.ingest([observation(ident=1),observation(ident=2,x=1.01)],0,100)
        self.assertEqual(len(t.tracks),2)
    def test_no_repeated_camera_confirmation(self):
        t=GlobalTracker();t.ingest([observation(f'MODULE{i}') for i in range(8)],0,100)
        self.assertFalse(t.output(0))
    def test_outlier(self):
        t=self.run_frames();t.ingest([observation('MODULE9',x=100)],1.,101.)
        self.assertEqual(len(t.tracks),2);self.assertLess(t.tracks[1].x[0],1)
    def test_static(self):
        t=GlobalTracker()
        for i in range(20):t.ingest([observation()],i*.2,100+i*.2)
        self.assertTrue(np.allclose(t.tracks[1].x,[1,1,0,0]))
    def test_no_id_collision(self):
        t=GlobalTracker(max_id=1);t.ingest([observation(ident=i,x=i*10) for i in range(3)],0,100)
        self.assertEqual(len(t.tracks),2)
    def test_late_never_refreshes(self):
        t=self.run_frames();last=t.tracks[1].last_real;t.ingest([observation()],.1,100.1)
        self.assertEqual(last,t.tracks[1].last_real)
    def test_class_policy(self):
        t=GlobalTracker(classes={'pallet':Policy(confirm_hits=1,publish_age=.1)})
        t.ingest([observation(cls='pallet')],0,100)
        self.assertTrue(t.output(0));self.assertFalse(t.output(.2))

class Ingress(unittest.TestCase):
    def setUp(self):
        self.now=0.;self.p=DataProcessing(clock=lambda:self.now,wall=lambda:100+self.now)
    def send(self, frame, **kwargs):
        self.p.on_message(None,None,message(packet(frame,**kwargs),kwargs.get('module','MODULE1')))
    def tick(self, n=.2):self.now+=n;return self.p.compute()
    def test_confirm_and_stale(self):
        self.send(0);self.tick();self.send(1);self.assertTrue(self.tick());self.assertFalse(self.tick(2))
    def test_empty_snapshot(self):
        self.send(0);self.tick();self.send(1);self.tick();self.send(2,entities=[])
        self.assertFalse(self.tick(1))
    def test_duplicate(self):
        self.send(0);self.send(0);self.assertEqual(self.p.rejected,1)
    def test_out_of_order(self):
        self.send(2);self.send(1);self.assertEqual(self.p.rejected,1)
    def test_restart_old_session(self):
        self.send(0);self.send(0,session='new');self.send(1);self.assertEqual(self.p.rejected,1)
    def test_retained(self):
        self.p.on_message(None,None,message(packet(),retain=True));self.assertEqual(self.p.rejected,1)
    def test_malformed(self):
        for p in [None, {}, {'version':3}, packet(entities=[{}]),packet(entities='bad')]:
            self.p.on_message(None,None,message(p))
        self.assertEqual(self.p.rejected,5)
    def test_nan(self):
        p=packet();p['entities'][0]['position'][0]=float('nan')
        self.p.on_message(None,None,message(p));self.assertEqual(self.p.rejected,1)
    def test_wrong_topic(self):
        self.p.on_message(None,None,message(packet(),'MODULE2'));self.assertEqual(self.p.rejected,1)
    def test_predicted(self):
        p=packet();p['entities'][0]['track_state']='predicted'
        self.p.on_message(None,None,message(p));self.tick();self.assertFalse(self.p.tracker.tracks)
    def test_legacy_consumed_once(self):
        self.p.on_message(None,None,message([{'id':1,'class':'person','position':[1,1]}]))
        self.tick();self.tick();self.assertEqual(self.p.tracker.tracks[1].hits,1)
    def test_clock_skew(self):
        p=packet(capture=200);p['clock_synchronized']=True
        self.p.on_message(None,None,message(p));self.assertEqual(self.p.rejected,1)
    def test_queue_bound(self):
        for i in range(300):self.send(i)
        self.assertLessEqual(len(self.p.pending),cfg.MAX_PENDING_SNAPSHOTS)
    def test_no_freshening_when_idle(self):
        self.send(0);self.tick();self.send(1);self.tick()
        stamp=self.p.tracker.tracks[1].wall
        self.tick(.1);self.assertEqual(stamp,self.p.tracker.tracks[1].wall)

class Local(unittest.TestCase):
    def detection(self,x=0, cls='person'):
        return types.SimpleNamespace(center=(x,0),class_name=cls,last_seen=-1,seen_count=0)
    def test_single(self):
        t=LocalTracker(min_hits=2);t.update([self.detection()],0);r=t.update([self.detection(1)],1)
        self.assertTrue(r[0].confirmed)
    def test_one_to_one(self):
        t=LocalTracker();t.update([self.detection()],0);r=t.update([self.detection(1),self.detection(2)],1)
        self.assertEqual(len(r),2)
    def test_occlusion_not_observed(self):
        t=LocalTracker(min_hits=1);t.update([self.detection()],0);r=t.update([],1)
        self.assertEqual(r[0].track_state,'occluded')
    def test_delete(self):
        t=LocalTracker(max_missed=2);t.update([self.detection()],0);self.assertFalse(t.update([],2))
    def test_no_local_id_reuse(self):
        t=LocalTracker(max_missed=1);t.update([self.detection()],0);t.update([],1)
        self.assertEqual(list(t.update([self.detection()],2)),[1])
    def test_crossing(self):
        t=LocalTracker(max_distance=50,min_hits=1)
        for f in range(6):
            r=t.update([self.detection(f*10),self.detection(100-f*10)],f)
        r=t.update([self.detection(60),self.detection(40)],6)
        self.assertEqual(r[0].center,(60,0));self.assertEqual(r[1].center,(40,0))
    def test_confirmation_requires_consecutive(self):
        t=LocalTracker(min_hits=3);t.update([self.detection()],0);t.update([],1);r=t.update([self.detection()],2)
        self.assertFalse(r[0].confirmed);self.assertEqual(r[0].seen_count,1)

class Geometry(unittest.TestCase):
    def test_no_map(self): self.assertEqual(quality([0,0],None),1)
    def test_soft_map(self): self.assertEqual(quality([100,100],{'polygon':[[0,0],[1,0],[1,1],[0,1]]}),.5)
    def test_footprint(self): self.assertEqual(len(footprint(0,0,5,25,51.4,39.4,1)),4)
    def test_horizon(self): self.assertIsNone(footprint(0,0,5,0,51.4,39.4,1))

if __name__=='__main__':unittest.main()

class AdditionalScenarios(unittest.TestCase):
    def test_global_crossing(self):
        t=GlobalTracker()
        for f in range(21):
            t.ingest([observation('MODULE1',1,x=f*.1),observation('MODULE1',2,x=2-f*.1)],f*.2,100+f*.2)
        self.assertGreater(t.tracks[1].x[0],1.8)
        self.assertLess(t.tracks[2].x[0],.2)
    def test_close_people_two_cameras(self):
        t=GlobalTracker()
        for f in range(4):
            t.ingest([observation('MODULE1',1,x=1),observation('MODULE1',2,x=1.3),observation('MODULE2',5,x=1.01),observation('MODULE2',6,x=1.31)],f*.2,100+f*.2)
        self.assertEqual(len(t.output(.6)['person']),2)
    def test_non_overlapping(self):
        t=GlobalTracker(Policy(confirm_hits=1));t.ingest([observation('MODULE1',x=0),observation('MODULE2',x=20)],0,100)
        self.assertEqual(len(t.output(0)['person']),2)
    def test_slow_edge_rejected(self):
        p=packet();p['processing_age']=2
        with self.assertRaises(ValueError):decode(p,'MODULE1',0,100)
    def test_old_observation_not_real(self):
        p=packet();p['entities'][0]['observation_age']=.2
        self.assertFalse(decode(p,'MODULE1',0,100).observations)
    def test_metrics(self):
        from tools.metrics import evaluate
        truth={0:[{'id':1,'class':'person','position':[0,0]}],1:[{'id':1,'class':'person','position':[1,0]}]}
        output={0:[{'id':5,'category':'person','position':[0,0]}],1:[{'id':5,'category':'person','position':[1,0]}]}
        r=evaluate(truth,output);self.assertEqual(r['idf1'],1);self.assertEqual(r['id_switches'],0)
        output[1][0]['id']=6;r=evaluate(truth,output);self.assertEqual(r['id_switches'],1);self.assertEqual(r['idf1'],.5)
