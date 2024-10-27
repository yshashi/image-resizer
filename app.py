from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import os
import schedule
import time
import threading
import datetime


scheduler = None  # Global variable to hold the scheduler

app = Flask(__name__)

IMAGE_SIZES = {
    'youtube-thumbnail': (1280, 720),
    'youtube-cover': (2560, 1440),
    'youtube-end-screen': (1920, 1080),
    'youtube-channel-art': (2560, 1440),
    'youtube-banner': (2560, 1440),

    'facebook-story': (1080, 1920),
    'facebook-square': (1200, 1200),
    'facebook-event-cover': (1920, 1080),
    'facebook-cover': (1600, 900),
    'facebook-post': (1200, 630),
    'facebook-ad': (1200, 628),
    'facebook-group-cover': (1640, 856),
    'facebook-cover-photo': (820, 312),

    'instagram-story': (1080, 1920),
    'instagram-portrait': (1080, 1350),
    'instagram-post': (1080, 1080),
    'instagram-landscape': (1080, 566)
}

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def cleanup_folder():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Removed {filename} at {datetime.datetime.now()}")
        except Exception as e:
            print(f"Error removing {filename} at {datetime.datetime.now()}: {str(e)}")

# Schedule the cleanup_folder function to run every 5 minutes
schedule.every(5).minutes.do(cleanup_folder)

def reset_scheduler():
    global scheduler
    if scheduler:
        # Stop the currently running scheduler
        schedule.clear(scheduler)

    # Create a new scheduler and schedule the cleanup_folder function
    scheduler = schedule.every(5).minutes.do(cleanup_folder)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'PATH': UPLOAD_FOLDER})


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    return jsonify({'message': 'Image uploaded successfully', 'filename': file.filename})

@app.route('/download/<filename>', methods=['GET'])
def download_image(filename):
    format = request.args.get('format', 'youtube-thumbnail')
    target_size = IMAGE_SIZES.get(format)

    if not target_size:
        return jsonify({'error': f'Invalid format: {format}'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return jsonify({'PATH': file_path})
    print(file_path)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    resized_image_path = resize_image(file_path, target_size, format)
    return send_file(resized_image_path, as_attachment=True)

def resize_image(file_path, target_size, format):
    resized_path = os.path.join(UPLOAD_FOLDER, f"{format}_{os.path.basename(file_path)}")
    
    with Image.open(file_path) as img:
        original_width, original_height = img.size
        target_width, target_height = target_size

        aspect_ratio = original_width / original_height
        if aspect_ratio > target_width / target_height:
            new_height = target_height
            new_width = int(aspect_ratio * new_height)
        else:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        left = (new_width - target_width) / 2
        top = (new_height - target_height) / 2
        right = (new_width + target_width) / 2
        bottom = (new_height + target_height) / 2

        img = img.crop((left, top, right, bottom))
        img.save(resized_path)

    return resized_path

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'message': 'File deleted successfully'})
    else:
        return jsonify({'error': 'File not found'}), 404

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    print("Starting Flask app and cleanup scheduler...")
    reset_scheduler()  # Schedule the cleanup_folder function initially
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    app.run(port=8100, debug=False)
