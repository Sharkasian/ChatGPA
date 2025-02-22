import requests
import json
import logging
import time
import os
from flask import Flask, request, jsonify

# Flask API URL for checking job status
FLASK_SERVER_URL = "http://127.0.0.1:5000"

# Persistent storage file
JOB_STATUS_FILE = "job_status.json"

# Load stored jobs from file
def load_job_status():
    if os.path.exists(JOB_STATUS_FILE):
        with open(JOB_STATUS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save jobs to file
def save_job_status():
    with open(JOB_STATUS_FILE, "w") as f:
        json.dump(job_status, f)

# Load existing jobs
job_status = load_job_status()

def generate_video_url(text):
    url = "https://api.sync.so/v2/generate"
    payload = {
        "input": [
            {
                "type": "text",
                "provider": {
                    "name": "elevenlabs",
                    "voiceId": "CwhRBWXzGAHq8TQ4Fs17",
                    "script": text
                }
            },
            {
                "type": "video",
                "url": "https://www.dropbox.com/scl/fi/0skjzczhpyfdtsmhpkf9l/ryanreynew.mp4?rlkey=1i1z1icg3tkoq8u1hlgfp158h&st=k6nwj4m9&raw=1"
            }
        ],
        "model": "lipsync-1.9.0-beta",
        "webhookUrl": "https://43b0-128-210-107-129.ngrok-free.app/webhook",
        "options": {"speedup": "2"}
    }
    headers = {
        "x-api-key": "sk-fOG2Mt8MS9mEWGYy37IKUA.nT8czmtxXfYSWE4GB1tzp2tJs9f7bbX-",
        "Content-Type": "application/json"
    }

    try:
        # Increase timeout to handle longer processing times
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response_data = response.json()

        if response.status_code in [200, 201]:
            real_id = response_data.get('id')
            if real_id:
                job_status[real_id] = {'status': 'in_progress', 'video_url': None}
                save_job_status()
                return real_id
        
    except requests.exceptions.RequestException as e:
        pass

    return None

def check_video_status(job_id):
    try:
        # Increase timeout to handle longer processing times
        response = requests.get(f"{FLASK_SERVER_URL}/status/{job_id}", timeout=120)
        data = response.json()

        if response.status_code == 200:
            status = data.get("status", "in_progress")
            video_url = data.get("video_url")
            if status == "completed":
                job_status[job_id] = {'status': status, 'video_url': video_url}
                save_job_status()
            return status, video_url
    except requests.exceptions.RequestException:
        pass
    return "in_progress", None

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    job_id = data.get('id')
    status = data.get('status')
    video_url = data.get('outputUrl')

    if job_id:
        job_status[job_id] = {'status': status, 'video_url': video_url}
        save_job_status()
        return jsonify({"message": "Status updated"}), 200

    return jsonify({"error": "Invalid data"}), 400

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    if job_id in job_status:
        return jsonify(job_status[job_id]), 200
    return jsonify({"status": "unknown", "video_url": None}), 404

if __name__ == "__main__":
    app.run(port=5000)