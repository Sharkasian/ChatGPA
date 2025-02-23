import json
import requests
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        session["username"] = username
        password = request.form.get("password")
        session["password"] = password

        # Only call scrape_brightspace if username and password are set
        # if username and password:
            # scrape_brightspace(username, password)
            # pdf_to_txt()
           
        # Debugging: Print session variables
        print(f"Session Username: {session.get('username')}, Session Password: {session.get('password')}")

        # You can add logic here to authenticate the user or perform other actions
        redirect_uri = url_for("callback", _external=True)
        return oauth.google.authorize_redirect(redirect_uri)
    else:
        redirect_uri = url_for("callback", _external=True)

    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    username = session.get("username")
    password = session.get("password")

    # Debugging: Print session variables
    print(f"Dashboard - Session Username: {username}, Session Password: {password}")

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

    return render_template("dashboardnew.html", events=formatted_events, user=username)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    # if request.method == "GET":
    #     return render_template("chat.html")

    if request.method == "POST":
        user_message = request.json.get("message", "")

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(user_message)
# prompttext = "You are a tutor in the subject of choice said after the colon. I want you to write a paragraph as how a teacher would explain the topic mentioned. I do not want a script but some paragraphs that generate the text: "
        # text_video = model.generate_content(prompttext + user_message)
        # session["text_video"] = text_video

            return jsonify({"reply": response.text})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route("/extract_exams", methods=["GET", "POST"])
def extract_exams():
    if request.method == "POST":
        if request.content_type != 'application/json':
            print("Unsupported Media Type:", request.content_type)  # Debugging line
            return jsonify({"error": "Unsupported Media Type. Content-Type must be 'application/json'"}), 415

        access_token = session.get("access_token")
        if not access_token:
            print("User not logged in")  # Debugging line
            return jsonify({"error": "User not logged in"}), 401

        try:
            # Read text file
            syllabus = load_text_file()
            if not syllabus:
                print("File is empty or missing")  # Debugging line
                return jsonify({"error": "File is empty or missing"}), 500

            model = genai.GenerativeModel("gemini-pro")

            promptInit = f"""
            Read through the following syllabus and summarize information about midterm and exam schedule,
            including name of the subject, dates, and times. Exclude exam schedule information that is TBA
            or undetermined, put all the information in a summarized text. Make sure to include the current year
            which is year of 2025, as well as the current month. Also include the course title which should be in the format
            similar to "MA26200" or "CS18000".
            
            \"\"\" 
            {syllabus}
            \"\"\"
            """
            response = model.generate_content(promptInit)
            raw_output = response.text.strip()
            print("Gemini Response:", raw_output)  # Debugging line

            prompt = f"""
            Extract exam subjects, their dates, and times from the following text:
            
            \"\"\"
            {response}
            \"\"\"

            Return only a JSON object:
            {{
                "exam_schedule": [
                    {{"subject": "Math Exam 1", "date": "YYYY-MM-DD", "time": "HH:MM-HH:MM"}},
                    {{"subject": "Physics Midterm 2", "date": "YYYY-MM-DD", "time": "HH:MM-HH:MM"}},
                    {{"subject": "Chemistry Midterm 1", "date": "YYYY-MM-DD", "time": "HH:MM-HH:MM"}}
                ]
            }}
            """

            response = model.generate_content(prompt)
            raw_output = response.text.strip()
            print("Gemini Response:", raw_output)  # Debugging line

            # Extract JSON portion from response
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                json_string = json_match.group(0)
                extracted_dates = json.loads(json_string)
            else:
                print("Invalid JSON format from Gemini")  # Debugging line
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
                    print("Invalid time range format")  # Debugging line
                    return jsonify({"error": "Invalid time range format"}), 400

                start_time_str, end_time_str = time_range
                start_time = datetime.strptime(f"{exam['date']} {start_time_str}", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(f"{exam['date']} {end_time_str}", "%Y-%m-%d %H:%M")

                event = {
                    "summary": exam["subject"],
                    "start": {
                        "dateTime": start_time.isoformat(),
                        "timeZone": "EST"
                    },
                    "end": {
                        "dateTime": end_time.isoformat(),
                        "timeZone": "EST"
                    }
                }

                response = requests.post(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers=headers,
                    json=event
                )

                if response.status_code != 200:
                    print(f"Failed to create event: {response.json()}")  # Debugging line
                    return jsonify({"error": response.json().get("error", "Failed to create event")}), response.status_code

            return jsonify({"message": "Events created successfully"}), 200

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")  # Debugging line
            return jsonify({"error": f"JSON decode error: {str(e)}"}), 500
        except Exception as e:
            print(f"Exception: {str(e)}")  # Debugging line
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid request method"}), 405



if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
