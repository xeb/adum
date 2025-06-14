from flask import Flask, render_template_string, request, jsonify
import requests
import yaml
import time
import json

app = Flask(__name__)

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_BASE = config['api']['base_url']
CAMERAS = config['cameras']

def make_api_request(endpoint, method='GET', data=None):
    """Make a request to the robot API"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            # Only send JSON if we have actual data, otherwise send empty JSON
            if data and data != {}:
                response = requests.post(url, json=data, timeout=5)
            else:
                response = requests.post(url, json={}, timeout=5)
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    """Main cyberpunk control interface"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>robotic_control_interface_v2.1</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono:wght@400&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background: #0a0a0a;
                color: #ff0040;
                font-family: 'Share Tech Mono', monospace;
                font-size: 12px;
                text-transform: lowercase;
                overflow-x: hidden;
                position: relative;
            }
            
            body::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: 
                    linear-gradient(90deg, transparent 98%, #ff004010 100%),
                    linear-gradient(0deg, transparent 98%, #ff004010 100%);
                background-size: 20px 20px;
                pointer-events: none;
                z-index: 1;
            }
            
            body::after {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(255, 0, 64, 0.03) 2px,
                    rgba(255, 0, 64, 0.03) 4px
                );
                pointer-events: none;
                z-index: 2;
            }
            
            .container {
                position: relative;
                z-index: 3;
                padding: 20px;
                max-width: 1600px;
                margin: 0 auto;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 15px;
                }
                
                body {
                    font-size: 14px;
                }
                
                .title {
                    font-size: 20px;
                }
                
                .panel-title {
                    font-size: 16px;
                }
            }
            
            @media (max-width: 480px) {
                .container {
                    padding: 10px;
                }
                
                .title {
                    font-size: 18px;
                }
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 1px solid #ff0040;
                padding-bottom: 20px;
            }
            
            .title {
                font-size: 24px;
                color: #ff0040;
                text-shadow: 0 0 10px #ff0040;
                margin-bottom: 10px;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 0.8; text-shadow: 0 0 5px #ff0040; }
                50% { opacity: 1; text-shadow: 0 0 20px #ff0040; }
            }
            
            .status-bar {
                background: #1a0000;
                border: 1px solid #ff0040;
                padding: 10px;
                margin-bottom: 20px;
                font-family: 'Share Tech Mono', monospace;
            }
            
            .main-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            @media (max-width: 768px) {
                .main-grid {
                    grid-template-columns: 1fr;
                    gap: 15px;
                }
            }
            
            .panel {
                background: rgba(26, 0, 0, 0.8);
                border: 1px solid #ff0040;
                padding: 15px;
                position: relative;
            }
            
            .panel::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, transparent, #ff0040, transparent);
                animation: scan 3s linear infinite;
            }
            
            @keyframes scan {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .panel-title {
                color: #ff0040;
                font-size: 14px;
                margin-bottom: 15px;
                text-transform: uppercase;
                border-bottom: 1px solid #ff004040;
                padding-bottom: 5px;
            }
            
            .control-group {
                margin-bottom: 15px;
            }
            
            .control-group label {
                display: block;
                color: #ff6666;
                margin-bottom: 5px;
                font-size: 11px;
            }
            
            input, button, select {
                background: #000;
                border: 1px solid #ff0040;
                color: #ff0040;
                font-family: 'Share Tech Mono', monospace;
                font-size: 11px;
                padding: 8px;
                text-transform: lowercase;
                touch-action: manipulation;
            }
            
            @media (max-width: 768px) {
                input, button, select {
                    font-size: 14px;
                    padding: 12px;
                    min-height: 44px;
                }
                
                button {
                    min-width: 120px;
                }
            }
            
            input:focus, select:focus {
                outline: none;
                box-shadow: 0 0 10px #ff004080;
                border-color: #ff6666;
            }
            
            button {
                cursor: pointer;
                background: #1a0000;
                transition: all 0.2s;
                min-width: 100px;
                margin: 2px;
            }
            
            button:hover {
                background: #ff0040;
                color: #000;
                box-shadow: 0 0 15px #ff0040;
            }
            
            button:active {
                transform: scale(0.95);
            }
            
            .coords-input {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 5px;
                margin-bottom: 10px;
            }
            
            .angles-input {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 5px;
            }
            
            @media (max-width: 480px) {
                .coords-input,
                .angles-input {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 8px;
                }
                
                .coords-input input:nth-child(5),
                .coords-input input:nth-child(6),
                .angles-input input:nth-child(5),
                .angles-input input:nth-child(6) {
                    grid-column: span 1;
                }
            }
            
            .button-row {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            }
            
            .cameras-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            @media (max-width: 768px) {
                .cameras-grid {
                    grid-template-columns: 1fr;
                    gap: 15px;
                }
            }
            
            @media (max-width: 480px) {
                .cameras-grid {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
            }
            
            .camera-panel {
                background: rgba(26, 0, 0, 0.6);
                border: 1px solid #ff0040;
                padding: 10px;
                position: relative;
            }
            
            .camera-title {
                color: #ff0040;
                font-size: 12px;
                margin-bottom: 10px;
                text-align: center;
            }
            
            .camera-feed {
                width: 100%;
                height: 200px;
                background: #000;
                border: 1px solid #ff004040;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ff004080;
            }
            
            .camera-feed img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }
            
            .log-panel {
                grid-column: 1 / -1;
                background: rgba(0, 0, 0, 0.9);
                border: 1px solid #ff0040;
                padding: 15px;
                height: 200px;
                overflow-y: auto;
            }
            
            .log-content {
                font-size: 10px;
                line-height: 1.4;
                white-space: pre-wrap;
            }
            
            .error { color: #ff4444; }
            .success { color: #ff6666; }
            .info { color: #ff0040; }
            
            .glitch {
                animation: glitch 0.3s;
            }
            
            @keyframes glitch {
                0% { transform: translate(0); }
                20% { transform: translate(-2px, 2px); }
                40% { transform: translate(-2px, -2px); }
                60% { transform: translate(2px, 2px); }
                80% { transform: translate(2px, -2px); }
                100% { transform: translate(0); }
            }
            
            .terminal-cursor::after {
                content: '▋';
                animation: blink 1s infinite;
            }
            
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title terminal-cursor">robotic_control_interface_v2.1</div>
                <div>connection established // robot_api_endpoint: {{ api_base }}</div>
            </div>
            
            <div class="status-bar">
                <span id="status">status: initializing...</span>
                <span style="float: right;" id="timestamp"></span>
            </div>
            
            <div class="main-grid">
                <!-- Movement Controls -->
                <div class="panel">
                    <div class="panel-title">movement_control</div>
                    
                    <div class="control-group">
                        <label>coordinates [x, y, z, rx, ry, rz]</label>
                        <div class="coords-input">
                            <input type="number" id="x" placeholder="x" step="0.1">
                            <input type="number" id="y" placeholder="y" step="0.1">
                            <input type="number" id="z" placeholder="z" step="0.1">
                            <input type="number" id="rx" placeholder="rx" step="0.1">
                            <input type="number" id="ry" placeholder="ry" step="0.1">
                            <input type="number" id="rz" placeholder="rz" step="0.1">
                        </div>
                        <button onclick="moveCoords()">move_to_coords</button>
                    </div>
                    
                    <div class="control-group">
                        <label>joint_angles [j1, j2, j3, j4, j5, j6]</label>
                        <div class="angles-input">
                            <input type="number" id="j1" placeholder="j1" step="0.1">
                            <input type="number" id="j2" placeholder="j2" step="0.1">
                            <input type="number" id="j3" placeholder="j3" step="0.1">
                            <input type="number" id="j4" placeholder="j4" step="0.1">
                            <input type="number" id="j5" placeholder="j5" step="0.1">
                            <input type="number" id="j6" placeholder="j6" step="0.1">
                        </div>
                        <button onclick="moveAngles()">move_to_angles</button>
                    </div>
                    
                    <div class="control-group">
                        <label>movement_speed</label>
                        <input type="range" id="speed" min="1" max="100" value="50">
                        <span id="speed-value">50</span>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="panel">
                    <div class="panel-title">quick_actions</div>
                    
                    <div class="button-row">
                        <button onclick="goHome()">go_home</button>
                        <button onclick="getRobotStatus()">get_status</button>
                        <button onclick="emergencyStop()">emergency_stop</button>
                    </div>
                    
                    <div class="button-row">
                        <button onclick="openGripper()">gripper_open</button>
                        <button onclick="closeGripper()">gripper_close</button>
                    </div>
                    
                    <div class="button-row">
                        <button onclick="performShuffle()">shuffle_sequence</button>
                        <button onclick="performWave()">wave_gesture</button>
                    </div>
                    
                    <div class="control-group">
                        <label>jog_control</label>
                        <select id="joint-select">
                            <option value="1">joint_1</option>
                            <option value="2">joint_2</option>
                            <option value="3">joint_3</option>
                            <option value="4">joint_4</option>
                            <option value="5">joint_5</option>
                            <option value="6">joint_6</option>
                        </select>
                        <input type="number" id="jog-increment" placeholder="increment" value="5" step="0.1">
                        <button onclick="jogJoint()">jog_joint</button>
                    </div>
                </div>
            </div>
            
            <!-- Camera Feeds -->
            <div class="cameras-grid">
                {% for camera in cameras %}
                <div class="camera-panel">
                    <div class="camera-title">{{ camera.name }} // {{ camera.device }}</div>
                    <div class="camera-feed">
                        <img id="cam-{{ camera.id }}" src="{{ api_base }}/video/frame/{{ camera.id }}" 
                             onerror="this.style.display='none'; this.parentNode.innerHTML='[camera_offline]';"
                             onload="this.style.display='block';">
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Log Panel -->
            <div class="log-panel">
                <div class="panel-title">system_log</div>
                <div class="log-content" id="log-content">
> initializing robotic control interface...
> loading configuration...
> establishing connection to robot api...
                </div>
            </div>
        </div>
        
        <script>
            const API_BASE = '{{ api_base }}';
            
            // Update timestamp
            function updateTimestamp() {
                document.getElementById('timestamp').textContent = 
                    'timestamp: ' + new Date().toISOString().toLowerCase();
            }
            setInterval(updateTimestamp, 1000);
            updateTimestamp();
            
            // Update speed display
            document.getElementById('speed').addEventListener('input', function() {
                document.getElementById('speed-value').textContent = this.value;
            });
            
            // Logging function
            function log(message, type = 'info') {
                const logContent = document.getElementById('log-content');
                const timestamp = new Date().toISOString().toLowerCase();
                const logLine = `${timestamp} > ${message}\\n`;
                logContent.textContent += logLine;
                logContent.scrollTop = logContent.scrollHeight;
                
                // Add glitch effect for errors
                if (type === 'error') {
                    document.body.classList.add('glitch');
                    setTimeout(() => document.body.classList.remove('glitch'), 300);
                }
            }
            
            // API request function
            async function makeRequest(endpoint, method = 'GET', data = null) {
                try {
                    document.getElementById('status').textContent = 'status: processing...';
                    
                    // Clean up endpoint - remove leading slash if present
                    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
                    
                    const options = {
                        method: method,
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    };
                    
                    // Always send JSON body for POST requests, even if empty
                    if (method === 'POST') {
                        options.body = JSON.stringify(data || {});
                    }
                    
                    const response = await fetch('/api/' + cleanEndpoint, options);
                    const result = await response.json();
                    
                    if (result.success) {
                        log(JSON.stringify(result.data, null, 2), 'success');
                        document.getElementById('status').textContent = 'status: ready';
                        return result.data;
                    } else {
                        log('error: ' + result.error, 'error');
                        document.getElementById('status').textContent = 'status: error';
                        return null;
                    }
                } catch (error) {
                    log('connection_error: ' + error.message, 'error');
                    document.getElementById('status').textContent = 'status: connection_failed';
                    return null;
                }
            }
            
            // Movement functions
            async function moveCoords() {
                const coords = [
                    parseFloat(document.getElementById('x').value) || 0,
                    parseFloat(document.getElementById('y').value) || 0,
                    parseFloat(document.getElementById('z').value) || 0,
                    parseFloat(document.getElementById('rx').value) || 0,
                    parseFloat(document.getElementById('ry').value) || 0,
                    parseFloat(document.getElementById('rz').value) || 0
                ];
                const speed = parseInt(document.getElementById('speed').value);
                
                log(`move_coords: [${coords.join(', ')}] speed: ${speed}`);
                await makeRequest('robot/move/coords', 'POST', { coords, speed });
            }
            
            async function moveAngles() {
                const angles = [
                    parseFloat(document.getElementById('j1').value) || 0,
                    parseFloat(document.getElementById('j2').value) || 0,
                    parseFloat(document.getElementById('j3').value) || 0,
                    parseFloat(document.getElementById('j4').value) || 0,
                    parseFloat(document.getElementById('j5').value) || 0,
                    parseFloat(document.getElementById('j6').value) || 0
                ];
                const speed = parseInt(document.getElementById('speed').value);
                
                log(`move_angles: [${angles.join(', ')}] speed: ${speed}`);
                await makeRequest('robot/move/angles', 'POST', { angles, speed });
            }
            
            async function jogJoint() {
                const joint_id = parseInt(document.getElementById('joint-select').value);
                const increment = parseFloat(document.getElementById('jog-increment').value) || 0;
                const speed = parseInt(document.getElementById('speed').value);
                
                log(`jog_joint: ${joint_id} increment: ${increment} speed: ${speed}`);
                await makeRequest('robot/jog', 'POST', { joint_id, increment, speed });
            }
            
            // Quick action functions
            async function goHome() {
                log('executing: go_home');
                await makeRequest('robot/home', 'POST');
            }
            
            async function getRobotStatus() {
                log('requesting: robot_status');
                await makeRequest('robot/status');
            }
            
            async function emergencyStop() {
                log('executing: emergency_stop');
                // This would need to be implemented in the API
                alert('emergency stop not implemented in api');
            }
            
            async function openGripper() {
                const speed = parseInt(document.getElementById('speed').value);
                log(`gripper_open: speed ${speed}`);
                await makeRequest('robot/gripper/open', 'POST', { speed });
            }
            
            async function closeGripper() {
                const speed = parseInt(document.getElementById('speed').value);
                log(`gripper_close: speed ${speed}`);
                await makeRequest('robot/gripper/close', 'POST', { speed });
            }
            
            async function performShuffle() {
                const speed = parseInt(document.getElementById('speed').value);
                log(`shuffle_sequence: speed ${speed}`);
                await makeRequest('robot/shuffle', 'POST', { speed, times: 3 });
            }
            
            async function performWave() {
                log('wave_gesture: executing');
                await makeRequest('robot/wave', 'POST');
            }
            
            // Refresh camera feeds
            function refreshCameras() {
                {% for camera in cameras %}
                const cam{{ camera.id }} = document.getElementById('cam-{{ camera.id }}');
                if (cam{{ camera.id }}) {
                    cam{{ camera.id }}.src = API_BASE + '/video/frame/{{ camera.id }}?t=' + Date.now();
                }
                {% endfor %}
            }
            
            // Initialize
            window.onload = function() {
                log('interface_initialized');
                getRobotStatus();
                
                // Auto-refresh cameras every 100ms for near real-time feed
                setInterval(refreshCameras, 100);
            };
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html, 
                                 api_base=API_BASE, 
                                 cameras=CAMERAS)

@app.route('/api/<path:endpoint>', methods=['GET', 'POST'])
def api_proxy(endpoint):
    """Proxy API requests to the robot controller"""
    try:
        data = None
        if request.method == 'POST':
            # Try to get JSON data, but don't fail if there isn't any
            try:
                data = request.get_json(force=True, silent=True)
            except:
                data = None
        
        result = make_api_request(f'/{endpoint}', request.method, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Proxy error: {str(e)}'})

if __name__ == '__main__':
    app.run(host=config['client']['host'], 
            port=config['client']['port'], 
            debug=config['client']['debug'])