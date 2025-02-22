import json
import requests
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request
from datetime import datetime, timedelta


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")  # Ensure this environment variable is set

oauth = OAuth(app)

oauth.register(
    "google",
    client_id=env.get("GOOGLE_CLIENT_ID"),
    client_secret=env.get("GOOGLE_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email https://www.googleapis.com/auth/calendar.readonly",
    },
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

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
def planner():
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

if __name__ == "__main__":
    app.run(host="localhost", port=env.get("PORT", 3001), debug=True)
