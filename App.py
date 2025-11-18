from flask import Flask, send_from_directory
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import os

# -----------------------
# CONFIG - MQTT
# -----------------------
MQTT_BROKER = "44.223.43.74"  # <- IP do broker MQTT
MQTT_PORT = 1883
MQTT_TOPIC = "smartworksense/dados"   # <- Mesmo tópico do ESP32

# -----------------------
# Flask + SocketIO
# -----------------------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Guarda últimos valores
dados = {"temp": 0, "lux": 0, "postura": 0, "inclinacao": 0}


# -----------------------
# MQTT - callbacks
# -----------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] ✓ Conectado com sucesso!")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] ✓ Subscrito em: {MQTT_TOPIC}")
    else:
        print(f"[MQTT] ✗ Falha na conexão! Código: {rc}")


def on_message(client, userdata, msg):
    global dados

    try:
        payload = msg.payload.decode()
        dados_recebidos = json.loads(payload)

        # Garante que as chaves existem
        dados["temp"] = dados_recebidos.get("temp", 0)
        dados["lux"] = dados_recebidos.get("lux", 0)
        dados["postura"] = dados_recebidos.get("postura", 0)
        dados["inclinacao"] = dados_recebidos.get("inclinacao", 0)

        print("[MQTT] Recebido:", dados)

        # Envia para TODOS os clientes conectados
        socketio.emit("novo_dado", dados, broadcast=True)
        print("[SocketIO] ✓ Dados enviados para o front!")

    except Exception as e:
        print("[ERRO MQTT]", e)


# -----------------------
# INICIALIZAÇÃO MQTT
# -----------------------
print(f"[MQTT] Tentando conectar em {MQTT_BROKER}:{MQTT_PORT}...")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("[MQTT] Loop iniciado. Aguardando dados...")
except Exception as e:
    print(f"[MQTT] ✗ ERRO ao conectar: {e}")


# -----------------------
# SocketIO - Eventos
# -----------------------
@socketio.on('connect')
def handle_connect():
    print("[SocketIO] ✓ Cliente conectado!")
    # Envia os últimos dados conhecidos
    socketio.emit('novo_dado', dados)


@socketio.on('disconnect')
def handle_disconnect():
    print("[SocketIO] ✗ Cliente desconectado!")


# -----------------------
# ROTA PRINCIPAL (Dashboard)
# -----------------------
@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "index.html")


# -----------------------
# Iniciar servidor Flask
# -----------------------
if __name__ == "__main__":
    print("🚀 Servidor iniciado em: http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
