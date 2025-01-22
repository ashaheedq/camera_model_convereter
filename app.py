import os
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, send_file
from flask_dropzone import Dropzone
from werkzeug.utils import secure_filename
from utils import undistort
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
import atexit

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'uploads'),
    DOWNLOAD_PATH=os.path.join(basedir, 'output'),
    DROPZONE_ALLOWED_FILE_CUSTOM='True',
    DROPZONE_ALLOWED_FILE_TYPE='.json',
    DROPZONE_DEFAULT_MESSAGE='Drop .json files to convert them',
    DROPZONE_MAX_FILE_SIZE=1024,
    DROPZONE_TIMEOUT=5 * 60 * 1000,
    SEND_FILE_MAX_AGE_DEFAULT=-1
)

dropzone = Dropzone(app)


def allowed_file(filename):
    return filename.split('.')[-1] == 'json'


@app.route('/', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        try:
            files = request.files.getlist('file')  # Handle multiple files
            ts = request.form.get('timestamp', '')  # Ensure timestamp is optional

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    new_filename = f'{filename.split(".")[0]}_{ts}.json'
                    save_location = os.path.join(app.config['UPLOADED_PATH'], new_filename)
                    file.save(save_location)

                    # Process the file
                    output_file = undistort(save_location, app.config['DOWNLOAD_PATH'])
                    
            # Clean up only after processing all files
            [f.unlink() for f in Path(app.config['UPLOADED_PATH']).glob("*") if f.is_file()]
        except Exception as e:
            print(f"Error: {e}")
            pass
    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    try:
        save_name = filename.split('_')[0] + '.json'
        return send_file(
            os.path.join(app.config['DOWNLOAD_PATH'], filename),
            mimetype='application/json',
            download_name=save_name,
            as_attachment=True
        )
    except Exception as e:
        print(f"Error: {e}")
        return "File not found", 404


@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(basedir, 'static'), 'favicon.ico')

def clean_download_folder():
    try:
        now = datetime.now()
        folder = app.config['DOWNLOAD_PATH']
        
        # Debugging: Check if folder exists
        if not os.path.exists(folder):
            print(f"Folder does not exist: {folder}")
            return
        
        print(f"Checking for files to delete in: {folder}")
        
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            
            if os.path.isfile(file_path):  # Check if it's a file
                file_creation_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_age = now - file_creation_time

                # Debugging: Log file details
                print(f"File: {filename}, Created: {file_creation_time}, Age: {file_age}")
                
                # Check if file is older than 24 hours
                if file_age > timedelta(hours=24):
                    os.remove(file_path)  # Delete the file
                    print(f"Deleted old file: {filename}")
                else:
                    print(f"File not old enough: {filename}")
            else:
                print(f"Skipped non-file: {filename}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

# Schedule the cleanup task
scheduler = BackgroundScheduler()
scheduler.add_job(clean_download_folder, 'interval', hours=24)
scheduler.start()

# Shut down the scheduler when the app stops
atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    clean_download_folder()
    app.run(debug=True)
