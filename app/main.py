import os
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, send_file
from flask_dropzone import Dropzone
from werkzeug.utils import secure_filename
from app.utils import undistort, remove_old_files
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.update(
    UPLOADED_PATH= os.path.join(basedir,'uploads'),
    DOWNLOAD_PATH= os.path.join(basedir, 'output'),
    DROPZONE_ALLOWED_FILE_CUSTOM='True',
    DROPZONE_ALLOWED_FILE_TYPE='.json',
    DROPZONE_MAX_FILE_SIZE = 1024,
    DROPZONE_TIMEOUT = 5*60*1000,
    SEND_FILE_MAX_AGE_DEFAULT= -1)

def allowed_file(filename):
    return filename.split('.')[-1] == 'json'
    
dropzone = Dropzone(app)
@app.route('/',methods=['POST','GET'])
def upload():
    # runs this everytime a user uploads a file
    remove_old_files(app.config['DOWNLOAD_PATH'])

    if request.method == 'POST':
        try:
            file = request.files['file']
            ts = request.form['timestamp']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                new_filename = f'{filename.split(".")[0]}_{ts}.json'
                save_location = os.path.join(app.config['UPLOADED_PATH'], new_filename)
                file.save(save_location)

                output_file = undistort(save_location)
                # Remove uploaded files 
                [f.unlink() for f in Path("uploads").glob("*") if f.is_file()] 
        except:
            pass    
    return render_template('index.html')
    
@app.route('/download/<filename>')
def download_file(filename):
    try:
        save_name = filename.split('_')[0] + '.json'
    except:
        pass
    return send_file(os.path.join(app.config['DOWNLOAD_PATH'], filename), mimetype='application/json', download_name=save_name, as_attachment=True)
