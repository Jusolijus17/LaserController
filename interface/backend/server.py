from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from constants import *
from dmx_controller import DMXController
from classes.Cue import Cue
from classes.SpiderHeadState import LEDCell
from rf_controller import RFController

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
dmx_values[SPIDER_HEAD_CHANNELS['redL']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['greenL']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['blueL']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['whiteL']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['redR']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['greenR']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['blueR']] = SPIDER_HEAD_COLOR_ON
dmx_values[SPIDER_HEAD_CHANNELS['whiteR']] = SPIDER_HEAD_COLOR_ON

# Création de l'instance de DMXController
rf_controller = RFController()
#rf_controller.setup()
dmx_controller = DMXController(dmx_values, rf_controller, olad_ip, olad_port, universe)

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

@app.route('/set_mh_gobo', methods=['POST'])
def set_mh_gobo():
    data = request.json
    gobo = data['gobo']
    dmx_controller.set_mh_gobo(gobo)
    return jsonify({'status': 'ok'})

@app.route('/set_mh_scene_gobo_switch', methods=['POST'])
def set_mh_scene_gobo_switch():
    data = request.json
    isOn = data['isOn']
    dmx_controller.set_mh_scene_gobo_switch(isOn)
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

@app.route('/set_sync_mode_for/<light>', methods=['POST'])
def set_sync_mode_for(light):
    data = request.json
    sync_modes = data['sync_modes'].split(',') if data['sync_modes'] else ''
    dmx_controller.set_sync_modes_for(light, sync_modes)
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

@app.route('/set_sh_led_selection', methods=['POST'])
def set_sh_led_selection():
    leds = request.json
    led_objects = [LEDCell.from_dict(led) for led in leds]
    dmx_controller.set_sh_led_selection(led_objects)
    return jsonify({'status': 'ok'})

@app.route('/set_master_slider_value', methods=['POST'])
def set_master_slider_value():
    data = request.json
    value = data['value']
    dmx_controller.set_master_strobe_chase(value)
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
    included_lights = data['lights']
    print(included_lights)
    dmx_controller.set_strobe_mode(included_lights)
    return jsonify({'status': 'ok'})

@app.route('/set_rf_strobe_on_off', methods=['POST'])
def set_rf_strobe_on_off():
    data = request.json
    isOn = data['isOn']
    rf_controller.set_strobe_on_off(isOn)
    return jsonify({'status': 'ok'})

@app.route('/set_rf_strobe_speed', methods=['POST'])
def set_rf_strobe_speed():
    data = request.json
    faster = data['faster']
    if faster:
        rf_controller.strobe_faster()
    else:
        rf_controller.strobe_slower()
    return jsonify({'status': 'ok'})

@app.route('/rf_strobe_reset', methods=['POST'])
def rf_strobe_reset():
    rf_controller.reset_strobe_speed(force=True)
    return jsonify({'status': 'ok'})

@app.route('/set_smoke_on_off', methods=['POST'])
def set_smoke_on_off():
    data = request.json
    isOn = data['isOn']
    rf_controller.set_smoke_on_off(isOn)
    return jsonify({'status': 'ok'})

@app.route('/set_pattern_include', methods=['POST'])
def set_pattern_include():
    data = request.json
    include_list = data['patterns']
    print(include_list)
    dmx_controller.set_laser_pattern_include(include_list)
    return jsonify({'status': 'ok'})

@app.route('/set_scene_for/<light>', methods=['POST'])
def set_mh_scene(light):
    data = request.json
    scene = data['scene']
    if light == 'movingHead':
        dmx_controller.set_mh_scene(scene)
    elif light == 'spiderHead':
        dmx_controller.set_sh_scene(scene)
        pass
    return jsonify({'status': 'ok'})

@app.route('/set_brightness_for/<light>', methods=['POST'])
def set_mh_brightness(light):
    data = request.json
    brightness = data['value']
    if light == 'movingHead':
        dmx_controller.set_mh_brightness(brightness)
    elif light == 'spiderHead':
        dmx_controller.set_sh_brightness(brightness)
    return jsonify({'status': 'ok'})

@app.route('/set_breathe_mode', methods=['POST'])
def set_breathe_mode():
    data = request.json
    included_lights = data['lights']
    print(included_lights)
    dmx_controller.set_breathe_mode(included_lights)
    return jsonify({'status': 'ok'})

@app.route('/set_strobe_speed_for/<light>', methods=['POST'])
def set_mh_strobe(light):
    data = request.json
    value = data['value']
    if light == 'movingHead':
        dmx_controller.set_mh_strobe_speed(value)
    elif light == 'spiderHead':
        dmx_controller.set_sh_strobe_speed(value)
    return jsonify({'status': 'ok'})

@app.route('/set_sh_chase_speed', methods=['POST'])
def set_sh_chase_speed():
    data = request.json
    speed = data['value']
    dmx_controller.set_sh_chase_speed(speed)
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

@app.route('/restore_state', methods=['POST'])
def restore_state():
    print("Restoring state...")
    dmx_controller.restore_state()
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
        
@socketio.on('sh_position_data')
def handle_sh_position_data(data):
    """
    Reçoit les données de position de la tête mobile via WebSocket, convertit en valeurs DMX,
    et met à jour les lumières.
    """
    # TODO: Convertir les données de position en valeurs DMX

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
