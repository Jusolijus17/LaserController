from email.mime import base
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from constants import COLORS, PATTERNS, MODES
from dmx_controler import start_sending_dmx, stop_sending_dmx

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Exemple de variable pour stocker le BPM (à synchroniser avec votre script de détection BPM)
current_bpm = 120
olad_ip = '192.168.2.52'
olad_port = 9090
universe = 1

base_url = f'http://{olad_ip}:{olad_port}'
dmx_values = [0] * 512

@socketio.on('tempo_update')
def handle_tempo_update(message):
    emit('tempo_update', message, broadcast=True)

@app.route('/set_olad_ip', methods=['POST'])
def set_olad_ip():
    global olad_ip
    olad_ip = request.json['olad_ip']
    return jsonify({'status': 'ok'})

@app.route('/set_mode', methods=['POST'])
def set_mode():
    data = request.json
    mode = data['mode']
    url = base_url + '/set_dmx'
    dmx_values[0] = MODES[mode]
    payload = {'u': universe, 'd': dmx_values}
    response = requests.post(url, data=payload)
    return jsonify({'status': 'sent' if response.status_code == 200 else 'error'})

@app.route('/set_pattern', methods=['POST'])
def set_pattern():
    data = request.json
    pattern = data['pattern']
    url = base_url + '/set_dmx'
    dmx_values[1] = PATTERNS[pattern]
    payload = {'u': universe, 'd': dmx_values}
    response = requests.post(url, data=payload)
    return jsonify({'status': 'sent' if response.status_code == 200 else 'error'})

@app.route('/set_sync_mode', methods=['POST'])
def set_sync_mode():
    data = request.json
    sync_mode = data['sync_mode']
    if sync_mode == 'pattern':
        start_sending_dmx()
    return jsonify({'status': 'ok'})

@app.route('/set_color', methods=['POST'])
def set_color():
    data = request.json
    color = data['color']
    url = base_url + '/set_dmx'
    dmx_values[8] = COLORS[color]
    payload = {'u': universe, 'd': dmx_values}
    response = requests.post(url, data=payload)
    return jsonify({'status': 'sent' if response.status_code == 200 else 'error'})

@app.route('/get_bpm', methods=['GET'])
def get_bpm():
    return jsonify({'bpm': current_bpm})

if __name__ == '__main__':
    socketio.run(app)
