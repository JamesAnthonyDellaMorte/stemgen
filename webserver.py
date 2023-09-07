from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask import Response
import os
import subprocess

app = Flask(__name__)
socketio = SocketIO(app)

UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'output/'

# Create directories if they don't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Global variable to store client session IDs
clients = {}

@app.route('/')
def index():
    return send_from_directory(".", "index.html")
@app.route('/output/<filename>')
def serve_output(filename):
    response = send_from_directory(OUTPUT_FOLDER, filename)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    
    if file.filename == '':
        return 'No selected file', 400
    
    if file:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        
        output_filename = os.path.join(OUTPUT_FOLDER, file.filename.replace('.wav', '.stem.m4a'))
        
        # Emitting a status update
        socketio.emit('status', {'message': 'Creating tags.json...'}, room=next(iter(clients.values())))
        
        # Run stemgen script
        cmd = ['python3', 'stemgen.py', "-d" ,"cuda", filename]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
       
        for line in process.stdout:
            # Check if the line contains progress information
            if "%" in line and "[" in line and "]" in line:
                # Emit the line as a status update
                socketio.emit('status', {'message': line.strip()}, room=next(iter(clients.values())))

        process.communicate()
        
        socketio.emit('status', {'message': 'Processing complete!', 'filename': os.path.basename(output_filename)}, room=next(iter(clients.values())))
        
        return send_from_directory(OUTPUT_FOLDER, os.path.basename(output_filename))
    return "Error"

@socketio.on('client_connected')
def handle_client_connect(data):
    clients[request.sid] = request.sid
@socketio.on('disconnect')
def handle_disconnect():
    clients.pop(request.sid, None)

if __name__ == '__main__':
    socketio.run(app, debug=True)
