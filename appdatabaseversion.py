from flask import Flask, render_template, redirect, url_for, request, session, g
import sqlite3
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json
from google.oauth2.credentials import Credentials
from calculations import calculate_average_score
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import pickle

app = Flask(__name__)
app.secret_key = "your_secret_key"

conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create table if not exists
try:
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

# Create table for goals if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    goal TEXT,
                    end_date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    days TEXT
                )
            ''')

    conn.commit()
except Exception as e:
    print("Error creating table:", e)

scopes = [
    'openid',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email'
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

def getting_creds():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'WebClient/client_secret_131606957380-ps44nt6hrpul20q162mke20i1e260kv4.apps.googleusercontent.com.json', scopes)
            creds = flow.run_local_server(port=5000)  # This starts the local server for authentication
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

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

    creds = getting_creds()
    service = build('calendar', 'v3', credentials=creds)
    calendar_list_entry = service.calendarList().get(calendarId='primary').execute() 
    session['email'] = calendar_list_entry['id']

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
        email = session.get('email')
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

    creds = getting_creds()
    service = build('calendar', 'v3', credentials=creds)


    # SAMPLE EVENT BEING CREATED FOR PRACTICE
    event = {
        'summary': 'Sample Event',
        'location': '123 Main St, Anytown, USA',
        'description': 'A chance to meet with friends.',
        'start': {
            'dateTime': '2024-05-30T09:00:00-07:00',
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': '2024-05-30T17:00:00-07:00',
            'timeZone': 'America/Los_Angeles',
        },
        'recurrence': [
            'RRULE:FREQ=DAILY;COUNT=2'
        ],
        'attendees': [
            {'email': 'friend1@example.com'},
            {'email': 'friend2@example.com'},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    # Call the Calendar API to create the event
    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

    try:
        service = build('calendar', 'v3', credentials=credentials)

        # Get all calendars in the user's account
        calendar_list = service.calendarList().list().execute()

        # Get all events from selected calendars for the current week
        start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_of_week = start_of_week + timedelta(days=7)

        all_events = []
        for calendar in calendar_list['items']:
            if calendar.get('selected'):
                calendar_id = calendar['id']
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_of_week.isoformat() + 'T00:00:00Z',
                    timeMax=end_of_week.isoformat() + 'T23:59:59Z',
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])
                all_events.extend(events)

        # Calculate the average score for events in the current week
        average_score = calculate_average_score(all_events)

        # Get Google Calendar URL
        google_calendar_url = get_google_calendar_url(credentials)

        return render_template('dashboard.html', google_calendar_url=google_calendar_url, average_score=average_score)

    except RefreshError:
        return redirect(url_for('index'))  # Redirect to index if credentials need to be refreshed


@app.route('/set_goal', methods=['POST'])
def set_goal():
    email = session.get('email')  # Assuming the email is stored in session after login
    goal = request.form.get('goal')
    end_date = request.form.get('endDate')
    start_time = request.form.get('startTime')
    end_time = request.form.get('endTime')
    days = request.form.getlist('days')

    # Convert days list to a comma-separated string
    days_str = ','.join(days)

    # Insert the goal into the database
    g.db.execute('INSERT INTO goals (email, goal, end_date, start_time, end_time, days) VALUES (?, ?, ?, ?, ?, ?)',
                 (email, goal, end_date, start_time, end_time, days_str))
    g.db.commit()

    return redirect(url_for('dashboard')) 


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

conn.close()