"""Legacy POS visualizer; all Tk operations run on the GUI thread."""
import json
import queue
import logging
import config as cfg
from tkinter import Tk, Canvas, Label
from connection import MQTTClient, ConnectionInfo
from visualizer_view import Viewport, draw_room, draw_entities


def main():
    logging.basicConfig(level=logging.INFO)
    window = Tk()
    window.title('Tracking Visualizer — coordinate in metri')
    view = Viewport.fit(
        getattr(cfg, 'VISUALIZER_ROOM_X', 18.226),
        getattr(cfg, 'VISUALIZER_ROOM_Z', 21.630),
        min(cfg.WIDTH, window.winfo_screenwidth() * .9),
        min(cfg.HEIGHT, window.winfo_screenheight() * .85),
        max(cfg.PADDING, 48),
    )
    window.resizable(False, False)
    canvas = Canvas(window, width=view.width, height=view.height,
                    background='#202830', highlightthickness=0)
    canvas.pack()
    status = Label(window, text=f'In attesa di messaggi su {cfg.LOCAL_PUB_TOPIC}', anchor='w')
    status.pack(fill='x')
    draw_room(canvas, view)
    latest = queue.Queue(maxsize=1)

    def receive(client, userdata, msg):
        try:
            entities = json.loads(msg.payload.decode())
            if not isinstance(entities, list):
                raise ValueError('POS must contain a list')
            try:
                latest.get_nowait()
            except queue.Empty:
                pass
            latest.put_nowait(entities)
        except (ValueError, UnicodeError, queue.Full):
            logging.warning('Invalid visualizer payload')

    def update():
        try:
            entities = latest.get_nowait()
        except queue.Empty:
            pass
        else:
            visible, outside, invalid = draw_entities(canvas, view, entities, cfg.DOT_WIDTH)
            status.config(text=f'{cfg.LOCAL_PUB_TOPIC} · visibili: {visible} · '
                               f'fuori area: {outside} · non validi: {invalid}')
        window.after(100, update)

    info = ConnectionInfo(cfg.VISUALIZER_MODULE_NAME, cfg.LOCAL_BROKER_IP_ADDRESS,
                          cfg.LOCAL_BROKER_PORT, cfg.LOCAL_PUB_TOPIC, 'null')
    conn = MQTTClient(info, on_message=receive)
    try:
        update()
        window.mainloop()
    finally:
        conn.stop()


if __name__ == '__main__':
    main()
