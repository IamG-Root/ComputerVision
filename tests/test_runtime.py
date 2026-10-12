"""Hardware-free checks: native camera/GUI are explicitly mocked."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Debug(unittest.TestCase):
    def load_drawing(self):
        self.cv=MagicMock();self.cv.error=RuntimeError
        self.config=types.SimpleNamespace(MODULE_NAME='TEST')
        self.utils=types.SimpleNamespace(import_exclusions=lambda:[],pixel_to_world=lambda x,y:(x,y),relative_to_absolute_position=lambda x,y:(x,y))
        with patch.dict(sys.modules,{'cv2':self.cv,'config':self.config,'utils':self.utils}):
            return load('drawing_test','module/drawing.py')
    def test_headless(self):
        d=self.load_drawing()
        with patch.dict('os.environ',{},clear=True):
            drawing=d.Drawing();drawing.draw(np.zeros((10,10,3)),{});self.assertFalse(drawing.exit())
            self.cv.namedWindow.assert_not_called()
    def test_close_window(self):
        d=self.load_drawing()
        with patch.dict('os.environ',{'DISPLAY':':0'}),patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)):
            drawing=d.Drawing();self.cv.waitKey.return_value=ord('q')
            self.assertFalse(drawing.exit());self.assertFalse(drawing.active)
    def test_frame_unchanged(self):
        d=self.load_drawing()
        with patch.dict('os.environ',{'DISPLAY':':0'}),patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)):
            drawing=d.Drawing();f=np.zeros((10,10,3));drawing.draw(f,{})
            shown=self.cv.imshow.call_args[0][1]
            self.assertIsNot(shown,f);self.assertTrue(np.array_equal(shown,f))
    def test_broken_display(self):
        d=self.load_drawing()
        with patch.dict('os.environ',{'DISPLAY':':0'}),patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)):
            drawing=d.Drawing();self.assertFalse(drawing.active)
    def test_all_flags(self):
        for target in ['module','server']:
            args=load('args_test',target+'/args.py')
            for flags in [[],['--draw'],['--debug'],['--draw','--debug']]:
                with patch.object(sys,'argv',['main.py']+flags):
                    a=args.parser();self.assertEqual(a.draw,'--draw' in flags);self.assertEqual(a.debug,'--debug' in flags)
    def test_logging(self):
        debug=load('debug_test','module/debug.py')
        e=types.SimpleNamespace(class_name='person',confidence=.9,track_state='observed',ground=(1,2),position=(1.,2.))
        with self.assertLogs(level='DEBUG') as logs:debug.Debugger().log(1,{2:e})
        self.assertIn('observed',logs.output[0])

class Connection(unittest.TestCase):
    def setUp(self):
        from tracking import mqtt
        self.m=mqtt
    def test_initial_failure_reconnect_async(self):
        with patch.object(self.m.mqtt,'Client') as factory:
            c=self.m.MQTTBase();c.configure('test','localhost',1883,'test/topic')
            factory.return_value.connect_async.assert_called_once()
            factory.return_value.loop_start.assert_called_once()
    def test_disconnect_does_not_recurse(self):
        with patch.object(self.m.mqtt,'Client'):
            c=self.m.MQTTBase();c.configure('test','localhost',1883,'test/topic')
            c.on_disconnect(None,None,None,1,None);self.assertFalse(c.isConnected)
            c.stop();self.assertTrue(c.should_stop);c.client.loop_stop.assert_called_once()
    def test_qos_and_retain(self):
        with patch.object(self.m.mqtt,'Client'):
            c=self.m.MQTTBase();c.configure('test','localhost',1883,'POS')
            c.on_connect(c.client,None,None,0,None);c.client.publish.return_value.rc=0
            self.assertTrue(c.send('[]'));c.client.publish.assert_called_once_with('POS','[]',qos=0,retain=False)
    def test_offline_drop(self):
        with patch.object(self.m.mqtt,'Client'):
            c=self.m.MQTTBase();c.configure('test','localhost',1883,'POS')
            self.assertFalse(c.send('[]'));c.client.publish.assert_not_called()

class EdgeLoop(unittest.TestCase):
    def run_edge(self, camera_failure=False, flags=None):
        flags=flags or []
        cfg=types.SimpleNamespace(PROTOCOL_VERSION=2)
        camera=MagicMock();camera.capture_timestamp=100.
        camera.capture_frame.side_effect=([RuntimeError('camera unavailable'),np.zeros((4,4,3))] if camera_failure else [np.zeros((4,4,3))])
        connection=MagicMock();drawing=MagicMock();inference=MagicMock()
        inference.extract_entities.return_value={};inference.entities={}
        modules={'config':cfg,'args':types.SimpleNamespace(parser=lambda:types.SimpleNamespace(draw='--draw' in flags,debug='--debug' in flags)),
            'inference':types.SimpleNamespace(Inference=lambda:inference),
            'connection':types.SimpleNamespace(MQTTClient=lambda:connection),
            'camera_stream':types.SimpleNamespace(CameraStream=lambda:camera),
            'drawing':types.SimpleNamespace(Drawing=lambda:drawing,NullDrawing=lambda:drawing),
            'debug':types.SimpleNamespace(Debugger=MagicMock,NullDebugger=MagicMock),
            'telemetry':types.SimpleNamespace(Telemetry=lambda:types.SimpleNamespace(snapshot=lambda *a:{'entities':[]}))}
        with patch.dict(sys.modules,modules):m=load('edge_main_test','module/main.py')
        signals={}
        def signal(sig,callback):signals[sig]=callback
        def sleep(dt):
            if dt==.2:signals[m.signal.SIGTERM]()
        with patch.object(m.signal,'signal',side_effect=signal),patch.object(m.time,'sleep',side_effect=sleep):m.main()
        self.assertEqual(connection.send.call_count,1);camera.stop.assert_called();connection.stop.assert_called()
        return connection.send.call_args
    def test_camera_recovery(self):self.run_edge(camera_failure=True)
    def test_debug_equivalence(self):
        calls=[self.run_edge(flags=f) for f in [[],['--draw'],['--debug'],['--draw','--debug']]]
        self.assertTrue(all(c==calls[0] for c in calls))

if __name__=='__main__':unittest.main()

class ServerShadow(unittest.TestCase):
    def test_no_publisher_in_shadow(self):
        conn=MagicMock();factory=MagicMock(return_value=conn)
        cfg=types.SimpleNamespace(SERVER_MODULE_NAME='SERVER',FIWARE_MODULE_NAME='FIWARE',LOCAL_BROKER_IP_ADDRESS='localhost',LOCAL_BROKER_PORT=1883,LOCAL_SUB_TOPIC='CV/#',LOCAL_PUB_TOPIC='POS',FIWARE_BROKER_IP_ADDRESS='localhost',FIWARE_BROKER_PORT=1883,FIWARE_SUB_TOPIC='$SYS/#',FIWARE_PUB_TOPIC='/secret_key_cam/cam_1/attrs',FLUSH_TIME=100000)
        modules={'config':cfg,'args':types.SimpleNamespace(parser=lambda:types.SimpleNamespace(draw=False,debug=False,shadow=True)),
            'connection':types.SimpleNamespace(MQTTClient=factory,ConnectionInfo=lambda **kw:types.SimpleNamespace(**kw)),
            'processing':types.SimpleNamespace(DataProcessing=MagicMock)}
        with patch.dict(sys.modules,modules):m=load('server_main_test','server/main.py')
        callbacks={}
        with patch.object(m.signal,'signal',side_effect=lambda sig,cb:callbacks.update({sig:cb})),patch.object(m.time,'sleep',side_effect=lambda _:callbacks[m.signal.SIGTERM]()):m.main()
        self.assertEqual(factory.call_count,1);conn.send.assert_not_called();conn.stop.assert_called_once()
        self.assertEqual(factory.call_args.kwargs['info'].client_id,'SERVER_SHADOW')

class Camera(unittest.TestCase):
    def test_sensor_timestamp_and_release(self):
        cv=MagicMock();cfg=types.SimpleNamespace(FRAME_RES_X=4,FRAME_RES_Y=4)
        with patch.dict(sys.modules,{'cv2':cv,'config':cfg,'picamera2':types.SimpleNamespace(Picamera2=MagicMock)}):m=load('camera_test','module/camera_stream.py')
        cam=m.CameraStream.__new__(m.CameraStream);cam.picam2=MagicMock()
        req=cam.picam2.capture_request.return_value
        req.get_metadata.return_value={'SensorTimestamp':9_000_000_000}
        req.make_array.return_value=np.zeros((4,4,3))
        with patch.object(m.time,'clock_gettime',return_value=10.),patch.object(m.time,'time',return_value=100.):cam.capture_frame()
        self.assertEqual(cam.capture_timestamp,99.);req.release.assert_called_once()
    def test_release_on_capture_error(self):
        cv=MagicMock();cfg=types.SimpleNamespace(FRAME_RES_X=4,FRAME_RES_Y=4)
        with patch.dict(sys.modules,{'cv2':cv,'config':cfg,'picamera2':types.SimpleNamespace(Picamera2=MagicMock)}):m=load('camera_test','module/camera_stream.py')
        cam=m.CameraStream.__new__(m.CameraStream);cam.picam2=MagicMock()
        req=cam.picam2.capture_request.return_value;req.get_metadata.return_value={};req.make_array.side_effect=RuntimeError('lost camera')
        with self.assertRaises(RuntimeError):cam.capture_frame()
        req.release.assert_called_once()
