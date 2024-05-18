from flask import Flask, render_template, redirect, url_for, request, session,g
import sqlite3
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json
from google.oauth2.credentials import Credentials
import logging

app = Flask(__name__)
app.secret_key = "your_secret_key"

conn = sqlite3.connect('data.db')
c = conn.cursor()
email = ''

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                scheduling TEXT,
                mental_health TEXT,
                large_parties NUMBER,
                networking_events NUMBER,
                friends_familiar NUMBER,
                zoom_meetings NUMBER,
                in_person_meetings NUMBER,
                lectures NUMBER,
                seminar_classes NUMBER,
                homework NUMBER,
                extra_activities NUMBER,
                working_out NUMBER,
                procrastinating NUMBER,
                sleep_hours_req NUMBER,
                sleep_hours_reg NUMBER,
                sleep TEXT,
                naps TEXT,
                activeness NUMBER,
                meditation TEXT,
                health_issues TEXT,
                dietary TEXT,
                caffeine TEXT,
                coffee NUMBER,
                drugs TEXT
            )
        ''')
conn.commit()

scopes = [
    'https://www.googleapis.com/auth/calendar.readonly'
]

# Define the flow globally
flow = Flow.from_client_secrets_file(
    'WebClient/client_secret_131606957380-ps44nt6hrpul20q162mke20i1e260kv4.apps.googleusercontent.com.json', 
    scopes=scopes,
    redirect_uri='http://localhost:5000/login'  # Redirect to login after Google authorization
)

# Function to get Google Calendar URL
def get_google_calendar_url(credentials):
    service = build('calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    primary_calendar_id = next((item['id'] for item in calendar_list['items'] if item.get('primary')), None)
    return f"https://calendar.google.com/calendar/embed?src={primary_calendar_id}&mode=WEEK"

def calculate_weight(duration):
    if duration >= timedelta(hours=2):
        return 40
    elif timedelta(hours=1) <= duration < timedelta(hours=2):
        return 25
    elif duration < timedelta(hours=1):
        return 10

# Function to calculate the average score for all events
def calculate_average_score(events):
    # print("average score being called")
    total_score = 0
    count = 0
    for event in events:
        start_time = event.get('start', {}).get('dateTime')
        end_time = event.get('end', {}).get('dateTime')
        if start_time and end_time:
            total_score += calculate_weight(datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time))
            count += 1
    # print(total_score / count if count > 0 else 0)
    return total_score / count if count > 0 else 0

@app.route('/')
def index():
    try:
        # Redirect to Google authentication
        authorization_url, state = flow.authorization_url(
            access_type='offline', prompt='select_account'
        )
        return redirect(authorization_url)
    except Exception as e:
        print("Error:", e)  # Print the error for debugging
        return "An error occurred during Google authentication", 500


@app.route('/login')
def login():
    # Fetch the access code from the request parameters
    access_code = request.args.get('code')
    if not access_code:
        return redirect(url_for('index'))  # Redirect to index if no access code

    # Exchange the access code for credentials
    credentials = flow.fetch_token(code=access_code)

    credentials_dict = credentials if isinstance(credentials, dict) else credentials.to_dict()

    # Store the credentials in the session
    session['credentials'] = json.dumps({
        'token': credentials_dict.get('access_token'),
        'refresh_token': credentials_dict.get('refresh_token'),
        'token_uri': flow.client_config['token_uri'],
        'client_id': flow.client_config['client_id'],
        'client_secret': flow.client_config['client_secret'],
        'scopes': credentials_dict.get('scope')
    })

    # Redirect to onboarding
    return redirect(url_for('onboarding'))


@app.before_request
def before_request():
    g.db = sqlite3.connect('data.db')

@app.after_request
def after_request(response):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
    return response


@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    # Retrieve credentials from session
    credentials_json = session.get('credentials')
    if not credentials_json:
        return redirect(url_for('index'))  # Redirect to index if no credentials
    
    credentials = json.loads(credentials_json)
    credentials = Credentials.from_authorized_user_info(credentials)

    g.conn = sqlite3.connect('data.db')
    print("route:", request.method)

    if request.method == 'POST':

        email = request.form.get('email')

        scheduling = request.form.get('scheduling')

        mental_health = request.form.get('mentalHealth')

        large_parties = request.form['Party/Concert/Rave/Large Dinners etc']

        networking_events = request.form['Networking Events']

        friends_familiar = request.form['Friend/people familiar with']

        zoom_meetings = request.form['Zoom/Virtual Meetings']

        in_person_meetings = request.form['In-Person Meetings']

        lectures = request.form['Lectures']

        seminar_classes = request.form['Seminar Classes']

        homework = request.form['Homework']

        extra_activities = request.form['Extracurricular Activities (add option where user can share what clubs stress/recharge them)']

        working_out = request.form['Working Out']

        procrastinating = request.form['Procrastinating']

        sleep_hours_req = request.form['sleepHoursreq']

        sleep_hours_reg = request.form['sleepHoursreg']

        sleep = request.form['sleep']

        naps = request.form['naps']

        activeness = request.form['activeness']

        meditation = request.form['meditation']

        health_issues = request.form['healthIssues']

        dietary = request.form['dietary']

        caffeine = request.form['caffeine']

        coffee = request.form['coffee']

        drugs = request.form['drugs']

        g.db.execute('INSERT INTO users (email, scheduling, mental_health, large_parties, networking_events, friends_familiar, zoom_meetings, \
                     in_person_meetings, lectures, seminar_classes, homework, extra_activities, working_out, procrastinating, sleep_hours_req, \
                     sleep_hours_reg , sleep, naps, activeness, meditation, health_issues, dietary, caffeine, coffee, drugs) VALUES (?, ?, ?, ?, \
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (email, scheduling, mental_health, large_parties, networking_events, friends_familiar, zoom_meetings, in_person_meetings, 
                       lectures, seminar_classes, homework, extra_activities, working_out, procrastinating, sleep_hours_req, sleep_hours_reg , 
                       sleep, naps, activeness, meditation, health_issues, dietary, caffeine, coffee, drugs))
        g.db.commit()
        return redirect(url_for('dashboard')) 
        
    return render_template('onboarding.html')
    

@app.route('/dashboard',  methods=['GET', 'POST'])
def dashboard():
    # Get credentials from session
    credentials_json = session.get('credentials')
    if not credentials_json:
        return redirect(url_for('index'))  # Redirect to index if no credentials

    # Convert credentials JSON to object
    credentials_info = json.loads(credentials_json)
    credentials = Credentials(
        token=credentials_info['token'],
        refresh_token=credentials_info['refresh_token'],
        token_uri=credentials_info['token_uri'],
        client_id=credentials_info['client_id'],
        client_secret=credentials_info['client_secret'],
        scopes=credentials_info['scopes']
    )

    service = build('calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    primary_calendar_id = next((item['id'] for item in calendar_list['items'] if item.get('primary')), None)
    
    # Get events for the current week
    start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
    end_of_week = start_of_week + timedelta(days=7)
    events_result = service.events().list(
        calendarId=primary_calendar_id,
        timeMin=start_of_week.isoformat() + 'T00:00:00Z',
        timeMax=end_of_week.isoformat() + 'T23:59:59Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Calculate the average score for events in the current week
    average_score = calculate_average_score(events)

    # Get Google Calendar URL
    google_calendar_url = get_google_calendar_url(credentials)

    return render_template('dashboard.html', google_calendar_url=google_calendar_url, average_score=average_score)



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)