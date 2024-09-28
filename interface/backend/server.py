from os import sync
from turtle import speed
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
dmx_controller = DMXController(dmx_values, olad_ip, olad_port, universe)

@app.route('/update_bpm', methods=['POST'])
def handle_update_bpm():
    """
    Route pour recevoir les mises à jour de BPM de bpmFinder.py
    et les relayer au frontend et à dmx_controller.
    """
    data = request.get_json()
    global current_bpm
    bpm = data.get('bpm')
    current_bpm = bpm
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
    dmx_controller.set_mode(mode)
    return jsonify({'status': 'ok'})

@app.route('/set_pattern', methods=['POST'])
def set_pattern():
    data = request.json
    pattern = data['pattern']
    dmx_controller.set_pattern(pattern)
    return jsonify({'status': 'ok'})

@app.route('/set_horizontal_animation', methods=['POST'])
def set_horizontal_animation():
    data = request.json
    enabled, speed = data['enabled'], data['speed']
    dmx_controller.set_horizontal_animation(enabled, speed)
    return jsonify({'status': 'ok'})

@app.route('/set_vertical_animation', methods=['POST'])
def set_vertical_animation():
    data = request.json
    enabled, speed = data['enabled'], data['speed']
    dmx_controller.set_vertical_animation(enabled, speed)
    return jsonify({'status': 'ok'})


@app.route('/set_sync_mode', methods=['POST'])
def set_sync_mode():
    data = request.json
    sync_modes = data['sync_modes'].split(',') if data['sync_modes'] else ''
    dmx_controller.set_sync_modes(sync_modes)
    return jsonify({'status': 'ok'})

@app.route('/set_bpm_multiplier', methods=['POST'])
def set_bpm_multiplier():
    data = request.json
    bpm_multiplier = data['multiplier']
    dmx_controller.set_multiplier(bpm_multiplier)
    return jsonify({'status': 'ok'})

@app.route('/set_vertical_adjust', methods=['POST'])
def set_vertical_adjust():
    data = request.json
    adjust = data['adjust']
    dmx_controller.set_vertical_adjust(adjust)
    return jsonify({'status': 'ok'})

@app.route('/set_color', methods=['POST'])
def set_color():
    data = request.json
    color = data['color']
    dmx_controller.set_color(color)
    return jsonify({'status': 'ok'})

@app.route('/get_bpm', methods=['GET'])
def get_bpm():
    global current_bpm
    response = jsonify({'bpm': current_bpm})
    return response

@app.route('/set_ola_ip', methods=['POST'])
def set_ola_ip():
    global olad_ip
    olad_ip = request.json['ip']
    dmx_controller.olad_ip = olad_ip
    return jsonify({'status': 'ok'})

@app.route('/set_ola_port', methods=['POST'])
def set_ola_port():
    global olad_port
    olad_port = request.json['port']
    dmx_controller.olad_port = olad_port
    return jsonify({'status': 'ok'})

@app.route('/get_ola_ip', methods=['GET'])
def get_ip():
    return jsonify({'ip': olad_ip, 'port': str(olad_port)})

@app.route('/set_strobe_mode', methods=['POST'])
def set_strobe_mode():
    data = request.json
    enabled = data['enabled']
    dmx_controller.set_strobe_mode(enabled)
    return jsonify({'status': 'ok'})

@app.route('/set_pattern_include', methods=['POST'])
def set_pattern_include():
    data = request.json
    include_list = data['patterns']
    print(include_list)
    dmx_controller.set_pattern_include(include_list)
    return jsonify({'status': 'ok'})

@app.route('/set_lights_include_color', methods=['POST'])
def set_lights_include_color():
    data = request.json
    include_list = data['lights']
    dmx_controller.set_lights_include_color(include_list)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_mode', methods=['POST'])
def set_mh_mode():
    data = request.json
    mode = data['mode']
    print("Setting mode to: ", mode)
    dmx_controller.set_mh_mode(mode)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_scene', methods=['POST'])
def set_mh_scene():
    data = request.json
    scene = data['scene']
    print("Setting scene to: ", scene)
    dmx_controller.set_mh_scene(scene)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_dimmer', methods=['POST'])
def set_mh_dimmer():
    data = request.json
    dimmer = data['value']
    dmx_controller.set_mh_dimmer(dimmer)
    return jsonify({'status': 'ok'})

@app.route('/send_single_strobe', methods=['POST'])
def send_single_strobe():
    dmx_controller.send_single_strobe()
    return jsonify({'status': 'ok'})

@app.route('/start_mh_strobe', methods=['POST'])
def start_mh_strobe():
    dmx_controller.start_mh_strobe()
    return jsonify({'status': 'ok'})

@app.route('/stop_mh_strobe', methods=['POST'])
def stop_mh_strobe():
    dmx_controller.stop_mh_strobe()
    return jsonify({'status': 'ok'})

@app.route('/set_mh_strobe', methods=['POST'])
def set_mh_strobe():
    data = request.json
    value = data['value']
    dmx_controller.set_mh_strobe(value)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_color_speed', methods=['POST'])
def set_mh_color_speed():
    data = request.json
    speed = data['speed']
    dmx_controller.set_mh_color_speed(speed)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
