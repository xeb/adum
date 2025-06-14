from flask import Flask, Response, request, jsonify
import cv2
import threading
import time
import os
from pymycobot import MechArm270

app = Flask(__name__)

# Robot arm initialization
try:
    arm = MechArm270("/dev/ttyAMA0", 1000000)
    print("Robot arm initialized successfully.")
except Exception as e:
    arm = None
    print(f"Error initializing robot arm: {e}")

# Thread-safe camera management
camera_lock = threading.Lock()
active_cameras = {}

def get_camera_stream(camera_id):
    """Get or create a camera stream for the given camera_id"""
    with camera_lock:
        if camera_id not in active_cameras:
            try:
                cap = cv2.VideoCapture(camera_id)
                if cap.isOpened():
                    active_cameras[camera_id] = cap
                else:
                    return None
            except Exception as e:
                print(f"Error opening camera {camera_id}: {e}")
                return None
        return active_cameras[camera_id]

def generate_frames(camera_id):
    """Generate video frames from camera"""
    cap = get_camera_stream(camera_id)
    if not cap:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               b'Error: Camera not available\r\n')
        return
        
    while True:
        try:
            with camera_lock:
                success, frame = cap.read()
            
            if not success:
                break
                
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                break
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error generating frame: {e}")
            break

# Robot Control API Endpoints

@app.route('/robot/status', methods=['GET'])
def robot_status():
    """Get current robot arm status"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    try:
        status = {
            "coords": arm.get_coords(),
            "angles": arm.get_angles(),
            "gripper": arm.get_gripper_value(),
            "error_info": arm.get_error_information(),
            "fresh_mode": arm.get_fresh_mode(),
            "gripper_protect_current": arm.get_gripper_protect_current(),
            "angles_coords": arm.get_angles_coords(),
            "HTS_gripper_torque": arm.get_HTS_gripper_torque(),
            "world_reference": arm.get_world_reference(),
            "tool_reference": arm.get_tool_reference(),
            "reference_frame": arm.get_reference_frame(),
            "movement_type": arm.get_movement_type()
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/move/coords', methods=['POST'])
def move_coords():
    """Move robot to specific coordinates"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    try:
        coords = data.get('coords', [])
        speed = data.get('speed', 50)
        
        if len(coords) != 6:
            return jsonify({"error": "Coordinates must be a list of 6 values [x, y, z, rx, ry, rz]"}), 400
            
        arm.send_coords(coords, speed)
        return jsonify({"success": True, "message": f"Moving to coordinates {coords} at speed {speed}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/move/angles', methods=['POST'])
def move_angles():
    """Move robot to specific joint angles"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    try:
        angles = data.get('angles', [])
        speed = data.get('speed', 50)
        
        if len(angles) != 6:
            return jsonify({"error": "Angles must be a list of 6 values [j1, j2, j3, j4, j5, j6]"}), 400
            
        arm.send_angles(angles, speed)
        return jsonify({"success": True, "message": f"Moving to angles {angles} at speed {speed}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/jog', methods=['POST'])
def jog_joint():
    """Jog a specific joint by increment"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    try:
        joint_id = data.get('joint_id', 1)
        increment = data.get('increment', 0)
        speed = data.get('speed', 50)
        
        if joint_id < 1 or joint_id > 6:
            return jsonify({"error": "Joint ID must be between 1 and 6"}), 400
            
        arm.jog_increment_angle(joint_id, increment, speed)
        return jsonify({"success": True, "message": f"Jogging joint {joint_id} by {increment} degrees at speed {speed}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/home', methods=['POST'])
def go_home():
    """Move robot to home position"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    # Accept JSON data but don't require it
    data = request.get_json(silent=True) or {}
        
    try:
        home_coords = [118.7, 83.8, 280.6, -86.04, -2.15, -55.0]
        arm.send_coords(home_coords, 100)
        return jsonify({"success": True, "message": "Moving to home position"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/gripper/open', methods=['POST'])
def open_gripper():
    """Open the gripper"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    data = request.get_json() or {}
    speed = data.get('speed', 100)
    
    try:
        arm.set_gripper_value(100, speed, 1)
        return jsonify({"success": True, "message": f"Opening gripper at speed {speed}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/gripper/close', methods=['POST'])
def close_gripper():
    """Close the gripper"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    data = request.get_json() or {}
    speed = data.get('speed', 100)
    
    try:
        arm.set_gripper_value(0, speed, 1)
        return jsonify({"success": True, "message": f"Closing gripper at speed {speed}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/shuffle', methods=['POST'])
def shuffle():
    """Perform shuffle movement"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    data = request.get_json() or {}
    speed = data.get('speed', 50)
    times = data.get('times', 2)
    
    try:
        # Start shuffle in a separate thread to avoid blocking
        def shuffle_movement():
            arm.send_coords([100.0, 0, 170, -175, 15, -170], speed)
            for i in range(times):
                arm.send_coords([100.0, 0, 170, -175, 15, -170], speed)
                time.sleep(0.1)
                arm.send_coords([170.0, 0, 170, -175, 15, -170], speed)
                time.sleep(0.1)
        
        shuffle_thread = threading.Thread(target=shuffle_movement)
        shuffle_thread.daemon = True
        shuffle_thread.start()
        
        return jsonify({"success": True, "message": f"Shuffling {times} times at speed {speed}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/robot/wave', methods=['POST'])
def wave():
    """Perform wave gesture"""
    if not arm:
        return jsonify({"error": "Robot arm not initialized"}), 500
        
    # Accept JSON data but don't require it
    data = request.get_json(silent=True) or {}
        
    try:
        def wave_movement():
            start = [100, -8, -40, 0, -70, -100]
            end = [105, 0, -40, 10, -30, -90]
            for _ in range(3):
                arm.send_angles(start, 100)
                time.sleep(0.5)
                arm.send_angles(end, 100)
                time.sleep(0.5)
        
        wave_thread = threading.Thread(target=wave_movement)
        wave_thread.daemon = True
        wave_thread.start()
        
        return jsonify({"success": True, "message": "Performing wave gesture"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Video Streaming API Endpoints

@app.route('/video/stream/<camera_id>')
def video_stream(camera_id):
    """Stream video from specified camera"""
    try:
        # Handle both integer and string camera IDs
        cam_id = int(camera_id) if camera_id.isdigit() else camera_id
        return Response(generate_frames(cam_id), 
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except ValueError:
        return jsonify({"error": "Invalid camera ID"}), 400

@app.route('/video/frame/<camera_id>')
def video_frame(camera_id):
    """Get single frame from specified camera"""
    try:
        cam_id = int(camera_id) if camera_id.isdigit() else camera_id
        cap = get_camera_stream(cam_id)
        
        if not cap:
            return jsonify({"error": "Camera not available"}), 404
            
        with camera_lock:
            success, frame = cap.read()
            
        if not success:
            return jsonify({"error": "Failed to capture frame"}), 500
            
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({"error": "Failed to encode frame"}), 500
            
        return Response(buffer.tobytes(), mimetype='image/jpeg')
    except ValueError:
        return jsonify({"error": "Invalid camera ID"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/video/cameras', methods=['GET'])
def list_cameras():
    """List available cameras"""
    available_cameras = []
    
    # Check common camera indices
    for i in range(5):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
            cap.release()
        except Exception:
            continue
    
    # Check common device paths
    device_paths = ['/dev/video0', '/dev/video1', '/dev/video2', '/dev/video3', '/dev/video4']
    for path in device_paths:
        if os.path.exists(path):
            available_cameras.append(path)
    
    return jsonify({"cameras": available_cameras})

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "robot_connected": arm is not None,
        "timestamp": time.time()
    })

# API documentation endpoint
@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        "robot_endpoints": {
            "GET /robot/status": "Get current robot status",
            "POST /robot/move/coords": "Move to coordinates {coords: [x,y,z,rx,ry,rz], speed: int}",
            "POST /robot/move/angles": "Move to joint angles {angles: [j1,j2,j3,j4,j5,j6], speed: int}",
            "POST /robot/jog": "Jog joint {joint_id: int, increment: float, speed: int}",
            "POST /robot/home": "Move to home position",
            "POST /robot/gripper/open": "Open gripper {speed: int}",
            "POST /robot/gripper/close": "Close gripper {speed: int}",
            "POST /robot/shuffle": "Shuffle movement {speed: int, times: int}",
            "POST /robot/wave": "Wave gesture"
        },
        "video_endpoints": {
            "GET /video/stream/<camera_id>": "Stream video from camera (MJPEG)",
            "GET /video/frame/<camera_id>": "Get single frame from camera (JPEG)",
            "GET /video/cameras": "List available cameras"
        },
        "utility_endpoints": {
            "GET /health": "Health check",
            "GET /api/docs": "API documentation"
        }
    }
    return jsonify(docs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8044, debug=True)
