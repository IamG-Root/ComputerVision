"""Legacy POS visualizer; all Tk operations run on the GUI thread."""
import json
import queue
import logging
import config as cfg
from tkinter import Tk, Canvas
from connection import MQTTClient, ConnectionInfo

def main():
    window=Tk();window.title('Tracking Visualizer')
    window.geometry(f'{cfg.WIDTH}x{cfg.HEIGHT}');window.resizable(False,False)
    canvas=Canvas(window,width=cfg.WIDTH,height=cfg.HEIGHT);canvas.pack()
    canvas.create_rectangle(cfg.PADDING,cfg.PADDING,cfg.WIDTH-cfg.PADDING,cfg.HEIGHT-cfg.PADDING,width=5,fill='gray')
    latest=queue.Queue(maxsize=1)
    def receive(client,userdata,msg):
        try:
            entities=json.loads(msg.payload.decode())
            if not isinstance(entities,list):return
            try:latest.get_nowait()
            except queue.Empty:pass
            latest.put_nowait(entities)
        except (ValueError,UnicodeError,queue.Full):logging.warning('Invalid visualizer payload')
    def update():
        try:
            entities=latest.get_nowait();canvas.delete('entity');canvas.delete('text')
            for e in entities:
                x,z=e['position'][0]/.011111,e['position'][1]/.011111
                canvas.create_oval(z-cfg.DOT_WIDTH,x-cfg.DOT_WIDTH,z+cfg.DOT_WIDTH,x+cfg.DOT_WIDTH,fill='yellow',tags='entity')
                canvas.create_text(z,x-25,text=f"ID: {e['id']} CLASS: {e['category']}",fill='yellow',tags='text')
        except queue.Empty:pass
        except (KeyError,TypeError,ValueError):logging.warning('Invalid POS entity')
        window.after(100,update)
    info=ConnectionInfo(cfg.VISUALIZER_MODULE_NAME,cfg.LOCAL_BROKER_IP_ADDRESS,cfg.LOCAL_BROKER_PORT,cfg.LOCAL_PUB_TOPIC,'null')
    conn=MQTTClient(info,on_message=receive)
    try:
        update();window.mainloop()
    finally:conn.stop()
if __name__=='__main__':main()
