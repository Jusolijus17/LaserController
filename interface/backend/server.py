from os import sync
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from constants import COLORS, PATTERNS, MODES
from dmx_controller import DMXController

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

# Création de l'instance de DMXController
dmx_controller = DMXController(dmx_values, olad_ip='192.168.2.52', olad_port=9090, universe=1)

@app.route('/update_bpm', methods=['POST'])
def handle_update_bpm():
    """
    Route pour recevoir les mises à jour de BPM de bpmFinder.py
    et les relayer au frontend et à dmx_controller.
    """
    data = request.get_json()
    bpm = data.get('bpm')
    if bpm:
        # Mise à jour du BPM dans DMXController
        dmx_controller.update_tempo(bpm)
        
        # Notification au frontend via WebSocket
        socketio.emit('bpm_update', {'bpm': bpm})
        return jsonify({'status': 'BPM updated', 'bpm': bpm}), 200
    else:
        return jsonify({'error': 'Invalid BPM data'}), 400

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

    default_pattern = next(iter(PATTERNS.values()))
    dmx_values[0] = 255 # Manual mode
    dmx_values[1] = PATTERNS.get(pattern, default_pattern)
    dmx_values_str = ','.join(map(str, dmx_values))

    payload = {'u': universe, 'd': dmx_values_str}
    response = requests.post(url, data=payload)
    
    return jsonify({'status': 'sent' if response.status_code == 200 else 'error'})


@app.route('/set_sync_mode', methods=['POST'])
def set_sync_mode():
    data = request.json
    sync_modes = data['sync_modes'].split(',') if data['sync_modes'] else ''
    print("Current sync mode: ", sync_modes)
    if sync_modes == '':
        dmx_controller.stop_sending_dmx()
    else:
        dmx_controller.start_sending_dmx(sync_modes)
    return jsonify({'status': 'ok'})

@app.route('/set_bpm_multiplier', methods=['POST'])
def set_bpm_multiplier():
    data = request.json
    bpm_multiplier = data['multiplier']
    dmx_controller.set_multiplier(bpm_multiplier)
    return jsonify({'status': 'ok'})

@app.route('/set_color', methods=['POST'])
def set_color():
    data = request.json
    color = data['color']
    url = base_url + '/set_dmx'

    default_color = next(iter(COLORS.values()))
    dmx_values[8] = COLORS.get(color, default_color)
    dmx_values_str = ','.join(map(str, dmx_values))

    payload = {'u': universe, 'd': dmx_values_str}
    response = requests.post(url, data=payload)

    return jsonify({'status': 'sent' if response.status_code == 200 else 'error'})

@app.route('/get_bpm', methods=['GET'])
def get_bpm():
    return jsonify({'bpm': current_bpm})

if __name__ == '__main__':
    socketio.run(app, debug=True)
