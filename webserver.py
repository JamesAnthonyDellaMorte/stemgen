from flask import Flask, request, send_from_directory
import os
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'outputs/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
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
        
        output_filename = os.path.join(OUTPUT_FOLDER, file.filename.replace('.wav', '.m4a'))
        
        # Run stemgen script
        cmd = ['python3', 'stemgen.py', filename]
        subprocess.run(cmd)
        
        # Assuming stemgen outputs the file in the specified format at the specified location
    return send_from_directory(OUTPUT_FOLDER, os.path.basename(output_filename))
@app.route('/')
def index():
    return send_from_directory(".", "index.html")
if __name__ == '__main__':
    app.run(debug=True)
