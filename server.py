import json
import requests
import jsonify
import re
import os
from os import environ as env

import google.generativeai as genai
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, jsonify
from datetime import datetime, timedelta

# custom functions
from scraper import scrape_brightspace
from pdf import pdf_to_txt


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")  # Ensure this environment variable is set
genai.configure(api_key=env.get("GEMINI_API_KEY"))

oauth = OAuth(app)

oauth.register(
    "google",
    client_id=env.get("GOOGLE_CLIENT_ID"),
    client_secret=env.get("GOOGLE_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email https://www.googleapis.com/auth/calendar.readonly",
        "scope": "openid profile email https://www.googleapis.com/auth/calendar.events",
    },
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

# Load local JSON file for debugging
def load_json_file(filename="exam_dates.json"):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except Exception as e:
        return {"error": str(e)}
    
def load_text_file():
    inputs_folder = os.path.join(os.getcwd(), "inputs")
    try:
        for filename in os.listdir(inputs_folder):
            if filename.endswith(".txt"):
                file_path = os.path.join(inputs_folder, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()
        return "No text files found in the inputs folder."
    except Exception as e:
        return str(e)


@app.route("/")
def home():
    return render_template(
        "homePage.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/callback")
def callback():
    token = oauth.google.authorize_access_token()
    session["user"] = token
    session["access_token"] = token["access_token"]
    return redirect("/dashboard")


@app.route("/login")
def login():
    redirect_uri = url_for("callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard", methods=["GET"])
def dashboard():
    user_info = session.get("user")

    session["user"] = {
        "name": user_info.get("name"),
        "email": user_info.get("email"),
    }
    user = session["user"].get("name")

    print(user)

    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {access_token}"}

    current_time = datetime.now()
    start_time = current_time.isoformat() + "Z"
    end_time = (current_time + timedelta(days=7)).isoformat() + "Z"

    events_response = requests.get(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events"
        f"?timeMin={start_time}&timeMax={end_time}&orderBy=startTime&singleEvents=true",
        headers=headers,
    )

    events_data = events_response.json()
    events = events_data.get("items", [])

    formatted_events = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

    for event in events:
        start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date"))
        end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date"))

        if start:
            event_date = datetime.strptime(start[:10], "%Y-%m-%d")
            weekday_name = event_date.strftime("%A")

            def format_time(time_str):
                """ Convert 24-hour time to 12-hour format with AM/PM """
                dt_obj = datetime.strptime(time_str[11:16], "%H:%M")
                return dt_obj.strftime("%I:%M %p")  # Converts to 'hh:mm AM/PM'

            formatted_events[weekday_name].append({
                "summary": event.get("summary", "No Title"),
                "start_time": format_time(start) if "T" in start else "All day",
                "end_time": format_time(end) if "T" in end else "All day"
            })

    # print(formatted_events)
    
    return render_template("dashboard.html", events=formatted_events, user=user)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return render_template("chat.html")

    user_message = request.json.get("message", "")

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/exams", methods=["GET", "POST"])
def extract_exam_dates():
    # scrape_brightspace("deng312", "Edzt6921!")
    # pdf_to_txt()
    
    if request.method == "POST" and request.content_type != 'application/json':
        return jsonify({"error": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"error": "User not logged in"}), 401

    try:
        # Read text file
        syllabus = load_text_file()
        print(syllabus)

        if not syllabus:
            return jsonify({"error": "File is empty or missing"}), 500

        model = genai.GenerativeModel("gemini-pro")

        promptInit = f"""
        Summarize the following syllabus document and focus on exam or midterm schedule information,
        exclude any exam information that is TBA or not determined yet:
        \"\"\" 
        {syllabus}
        \"\"\"
        """

        responseInit = model.generate_content(promptInit)
        raw_output = responseInit.text.strip()
        print("Gemini Response:", raw_output)  # Debugging line

        prompt = f"""
        Go through the following syllabus document, look for any midterm or exam, 
        use the year 2025 and the curret month information to help you,
        extrac only the valid dates, and times:
        
        \"\"\" 
        {responseInit}
        \"\"\"

        Return a JSON object with the following structure:
        {{
            "exam_schedule": [
                {{"subject": "Math", "date": "YYYY-MM-DD", "time": "HH:MM-HH:MM"}},
                {{"subject": "Physics", "date": "YYYY-MM-DD", "time": "HH:MM-HH:MM"}},
                {{"subject": "Chemistry", "date": "YYYY-MM-DD", "time": "HH:MM-HH:MM"}}
            ]
        }}
        """
        # print(syllabus)

        response = model.generate_content(prompt)
        raw_output = response.text.strip()
        print("Gemini Response:", raw_output)  # Debugging line

        # Extract JSON portion from response
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
            extracted_dates = json.loads(json_string)
        else:
            return jsonify({"error": "Invalid JSON format from Gemini"}), 500

        # Add events to Google Calendar
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        for exam in extracted_dates["exam_schedule"]:
            # Split the time range into start and end times
            time_range = exam["time"].split('-')
            if len(time_range) != 2:
                return jsonify({"error": "Invalid time range format"}), 400

            start_time_str, end_time_str = time_range
            start_time = datetime.strptime(f"{exam['date']} {start_time_str}", "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(f"{exam['date']} {end_time_str}", "%Y-%m-%d %H:%M")

            event = {
                "summary": exam["subject"],
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC"
                }
            }

            response = requests.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=headers,
                json=event
            )

            if response.status_code != 200:
                return jsonify({"error": response.json().get("error", "Failed to create event")}), response.status_code

        return jsonify({"message": "Events created successfully"}), 200

    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON decode error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
