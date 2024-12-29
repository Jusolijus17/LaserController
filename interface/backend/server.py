from os import sync
from turtle import speed
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from constants import LASER_CHANNELS, LASER_COLORS, LASER_PATTERNS, LASER_MODES
from dmx_controller import DMXController
from classes.Cue import Cue

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
dmx_values[LASER_CHANNELS['pattern']] = LASER_PATTERNS['straight']

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

@app.route('/set_mode_for/<light>', methods=['POST'])
def set_mode(light):
    data = request.json
    mode = data['mode']
    dmx_controller.set_mode_for(light, mode)
    return jsonify({'status': 'ok'})

@app.route('/set_pattern', methods=['POST'])
def set_pattern():
    data = request.json
    pattern = data['pattern']
    dmx_controller.set_laser_pattern(pattern)
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
    if not isinstance(data, list):
        return jsonify({'error': 'Invalid data format. Expected a list.'}), 400

    # Traite chaque lumière et sa couleur
    for entry in data:
        light = entry.get('light')
        color = entry.get('color')

        if not light or not color:
            return jsonify({'error': 'Missing light or color in entry.'}), 400

        # Appelle le contrôleur DMX pour chaque lumière
        dmx_controller.set_color(color, light)

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

@app.route('/set_strobe_mode_for/<light>', methods=['POST'])
def set_strobe_mode(light):
    data = request.json
    enabled = data['enabled']
    dmx_controller.set_strobe_mode(enabled, light)
    return jsonify({'status': 'ok'})

@app.route('/set_pattern_include', methods=['POST'])
def set_pattern_include():
    data = request.json
    include_list = data['patterns']
    print(include_list)
    dmx_controller.set_laser_pattern_include(include_list)
    return jsonify({'status': 'ok'})

@app.route('/set_lights_include_color', methods=['POST'])
def set_lights_include_color():
    data = request.json
    include_list = data['lights']
    print(include_list)
    dmx_controller.set_lights_include_color(include_list)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_scene', methods=['POST'])
def set_mh_scene():
    data = request.json
    scene = data['scene']
    dmx_controller.set_mh_scene(scene)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_brightness', methods=['POST'])
def set_mh_brightness():
    data = request.json
    brightness = data['value']
    dmx_controller.set_mh_brightness(brightness)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_breathe', methods=['POST'])
def set_mh_breathe():
    data = request.json
    enabled = data['breathe']
    dmx_controller.set_mh_breathe(enabled)
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
    dmx_controller.set_mh_color(None, speed)
    return jsonify({'status': 'ok'})

@app.route('/set_cue', methods=['POST'])
def set_cue():
    data = request.json
    cue = Cue.from_dict(data)
    dmx_controller.set_cue(cue)
    return jsonify({'status': 'ok'})

@socketio.on('gyro_data')
def handle_gyro_data(data):
    """
    Reçoit les données du gyroscope via WebSocket, convertit en valeurs DMX,
    et met à jour les lumières.
    """
    pan = data.get('pan')  # Angle du gyroscope (en degrés)
    tilt = data.get('tilt')  # Angle du gyroscope (en degrés)
    if pan is not None and tilt is not None:
        # Envoyer les valeurs DMX au contrôleur
        dmx_controller.set_pan_tilt(pan, tilt)
        emit('update_status', {'status': 'success'}, broadcast=True)
        print(f"Gyro Data - Pan: {pan}, Tilt: {tilt}")
    else:
        emit('update_status', {'status': 'error', 'message': 'Invalid data'}, broadcast=True)
        print("Invalid data")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
