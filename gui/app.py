import subprocess
import threading
import queue
import time
import signal
import os
import psutil
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Path to the scripts directory from the gui folder
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
# Path to the data directory for properties.json
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "objaverse")
# Path to the config.json file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "config.json")

running_processes = {}

def stream_script_output(script_name, args, session_id):
    """Helper function to run a shell script and stream output via WebSocket."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    command = ["/bin/bash", script_path]
    
    # The shell script will pass these to the python script
    command.extend(args)
    
    try:
        # Using Popen to get real-time output
        # Start new process group to better handle child processes
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            cwd=os.path.join(SCRIPTS_DIR, ".."),  # Run from the project root
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Track the process for this session
        running_processes[session_id] = process
        
        # Send initial status
        socketio.emit('script_started', {'message': 'Script started...'}, room=session_id)
        
        # Stream stdout
        def stream_stdout():
            for line in iter(process.stdout.readline, ''):
                if line:
                    socketio.emit('script_output', {
                        'type': 'stdout',
                        'data': line.rstrip()
                    }, room=session_id)
            process.stdout.close()
        
        # Stream stderr
        def stream_stderr():
            for line in iter(process.stderr.readline, ''):
                if line:
                    socketio.emit('script_output', {
                        'type': 'stderr',
                        'data': line.rstrip()
                    }, room=session_id)
            process.stderr.close()
        
        # Start streaming threads
        stdout_thread = threading.Thread(target=stream_stdout)
        stderr_thread = threading.Thread(target=stream_stderr)
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Wait for streaming threads to finish
        stdout_thread.join()
        stderr_thread.join()
        
        # Remove process from tracking
        if session_id in running_processes:
            del running_processes[session_id]
        
        if return_code == 0:
            socketio.emit('script_completed', {
                'success': True,
                'message': 'Script completed successfully'
            }, room=session_id)
        elif return_code == -signal.SIGKILL:
            socketio.emit('script_stopped', {
                'message': 'Script was stopped by user'
            }, room=session_id)
        else:
            socketio.emit('script_completed', {
                'success': False,
                'message': f'Script failed with return code {return_code}'
            }, room=session_id)
            
    except FileNotFoundError:
        # Remove process from tracking
        if session_id in running_processes:
            del running_processes[session_id]
        socketio.emit('script_error', {
            'error': f'Script not found: {script_path}'
        }, room=session_id)
    except Exception as e:
        # Remove process from tracking
        if session_id in running_processes:
            del running_processes[session_id]
        socketio.emit('script_error', {
            'error': f'Error running script: {str(e)}'
        }, room=session_id)

def run_script(script_name, args):
    """Helper function to run a shell script and capture output."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    command = ["/bin/bash", script_path]
    
    command.extend(args)
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.join(SCRIPTS_DIR, "..")
        )
        return {"success": True, "output": result.stdout, "error": result.stderr}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.stdout, "error": e.stderr}
    except FileNotFoundError:
        return {"success": False, "error": f"Script not found: {script_path}"}


@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/api/objects')
def get_objects():
    """Get available objects and their properties from properties.json."""
    try:
        properties_path = os.path.join(DATA_DIR, 'properties.json')
        with open(properties_path, 'r') as f:
            objects_data = json.load(f)
        return jsonify({"success": True, "objects": objects_data})
    except FileNotFoundError:
        return jsonify({"success": False, "error": "Properties file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid properties file format"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration from config.json."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
        return jsonify({"success": True, "config": config_data})
    except FileNotFoundError:
        return jsonify({"success": False, "error": "Config file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid config file format"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration in config.json."""
    try:
        # Get the new config data from request
        new_config = request.get_json()
        
        if not new_config:
            return jsonify({"success": False, "error": "No configuration data provided"}), 400
        
        # Read current config to preserve any fields not being updated
        try:
            with open(CONFIG_PATH, 'r') as f:
                current_config = json.load(f)
        except FileNotFoundError:
            current_config = {}
        
        customizable_fields = [
            'properties_json', 'base_scene_blendfile', 'shape_dir', 'material_dir',
            'output_image_dir', 'output_scene_dir', 'output_scene_file', 'masks_dir',
            'enhanced_image_dir', 'use_gpu', 'width', 'height', 'render_tile_size'
        ]
        
        for field in customizable_fields:
            if field in new_config:
                current_config[field] = new_config[field]
        
        # Write updated config back to file
        with open(CONFIG_PATH, 'w') as f:
            json.dump(current_config, f, indent=2)
        
        return jsonify({"success": True, "message": "Configuration updated successfully"})
        
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid JSON data"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Error updating config: {str(e)}"}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    print(f'Client connected: {request.sid}')
    emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    session_id = request.sid
    print(f'Client disconnected: {session_id}')
    
    # Clean up any running processes for this session
    if session_id in running_processes:
        try:
            process = running_processes[session_id]
            force_kill_process(process)
            del running_processes[session_id]
        except:
            pass

def force_kill_process(process):
    """Forcefully kill a process and all its children."""
    try:
        # Try to get all child processes
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        
        # Kill all child processes first
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        
        # Kill the main process
        parent.kill()
        
        # Wait for process to actually terminate
        process.wait(timeout=2)
        return True
    except (psutil.NoSuchProcess, subprocess.TimeoutExpired):
        try:
            # Fallback: kill entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            return True
        except (OSError, ProcessLookupError):
            return False
    except Exception:
        return False

@socketio.on('stop_script')
def handle_stop_script():
    """Handle script stop request via WebSocket."""
    session_id = request.sid
    
    if session_id in running_processes:
        try:
            process = running_processes[session_id]
            
            if force_kill_process(process):
                emit('script_stopped', {'message': 'Script force stopped'})
            else:
                emit('script_error', {'error': 'Failed to stop script - process may still be running'})
                
        except Exception as e:
            emit('script_error', {'error': f'Error stopping script: {str(e)}'})
    else:
        emit('script_error', {'error': 'No running script to stop'})

@socketio.on('start_script')
def handle_start_script(data):
    """Handle script execution request via WebSocket."""
    session_id = request.sid
    script_name = data.get('script_name')
    args = data.get('args', [])
    
    # Start script execution in a separate thread
    thread = threading.Thread(
        target=stream_script_output,
        args=(script_name, args, session_id)
    )
    thread.daemon = True
    thread.start()

@app.route('/run', methods=['POST'])
def run_render():
    """Handle form submission and run the appropriate script."""
    form_data = request.get_json()
    render_type = form_data.pop('render_type', None)
    
    args = []
    for key, value in form_data.items():
        if value:
            arg_key = f"--{key}"
            
            if isinstance(value, bool) and value:
                args.append(arg_key)
            elif key == 'objects':
                args.append(arg_key)
                args.extend(value.split())
            elif not isinstance(value, bool):
                args.append(arg_key)
                args.append(str(value))

    if render_type == 'single' or render_type == 'multiple':
        script_name = 'render.sh'
    else:
        return jsonify({"success": False, "error": "Invalid render type specified."}), 400

    result = run_script(script_name, args)
    return jsonify(result)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
