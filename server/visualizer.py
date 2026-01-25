import json
import config as cfg
from tkinter import *
from connection import MQTTClient, ConnectionInfo

def update_canvas(canvas):
    def on_message(client, userdata, msg):
        canvas.delete("entity")
        canvas.delete("text")
        entities = json.loads(msg.payload.decode('utf-8'))
        for entity in entities:
            x = entity["position"][0] / 0.011111
            y = entity["position"][1] / 0.011111
            canvas.create_oval(y - cfg.DOT_WIDTH, x - cfg.DOT_WIDTH, y + cfg.DOT_WIDTH, x + cfg.DOT_WIDTH, fill='yellow', tags="entity")
            canvas.create_text(y, x - 25, text=f"ID: {entity['id']}\nCLASS: {entity['class']}", font=("Consolas", 10, "bold"), fill="yellow", tags="text")
    return on_message

def init_canvas(window):
    canvas = Canvas(window, width=cfg.WIDTH, height=cfg.HEIGHT)
    canvas.pack()
    canvas.create_rectangle(cfg.PADDING, cfg.PADDING, cfg.WIDTH - cfg.PADDING, cfg.HEIGHT - cfg.PADDING, width=5, fill='gray')
    return canvas

def init_window():
    window = Tk()
    window.title("Tracking Visualizer")
    window.geometry(f"{cfg.WIDTH}x{cfg.HEIGHT}")
    window.resizable(False, False)
    return window

def main():
    window = init_window()
    canvas = init_canvas(window)
    infoLocalConnection = ConnectionInfo(
        client_id=cfg.VISUALIZER_MODULE_NAME,
        broker_ip=cfg.LOCAL_BROKER_IP_ADDRESS,
        broker_port=cfg.LOCAL_BROKER_PORT,
        sub_topic=cfg.LOCAL_PUB_TOPIC,
        pub_topic="null"
    )
    local_conn = MQTTClient(info=infoLocalConnection, on_message=update_canvas(canvas))
    window.mainloop()
    local_conn.stop()

if __name__ == "__main__":
    main()