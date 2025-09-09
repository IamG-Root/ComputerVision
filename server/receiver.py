import paho.mqtt.client as mqtt

# Configura i parametri del broker
BROKER_ADDRESS = "localhost"  # oppure l'indirizzo IP del broker
BROKER_PORT = 1883            # porta standard MQTT
MQTT_TOPIC = "CV/#"

# Funzione chiamata quando ci si connette al broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connesso al broker MQTT")
        client.subscribe(MQTT_TOPIC)
        print(f"Iscritto al topic '{MQTT_TOPIC}'")
    else:
        print(f"Connessione fallita con codice di errore {rc}")

# Funzione chiamata alla ricezione di un messaggio
def on_message(client, userdata, msg):
    print(f"{msg.topic}:\n{msg.payload.decode('utf-8')}")

# Crea un client MQTT
client = mqtt.Client()

# Collega le funzioni di callback
client.on_connect = on_connect
client.on_message = on_message

# Connessione al broker
try:
    client.connect(BROKER_ADDRESS, BROKER_PORT, keepalive=60)
    print("Tentativo di connessione al broker...")
except Exception as e:
    print(f"Errore durante la connessione: {e}")
    exit(1)

# Avvia il loop per mantenere attiva la connessione e gestire i messaggi
client.loop_forever()


