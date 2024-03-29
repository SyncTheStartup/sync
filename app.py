from flask import Flask, render_template, redirect, url_for, request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# Define the flow globally
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret_131606957380-u4ikuhues6u5s60dtueah3mgncn9u2u1.apps.googleusercontent.com.json', 
    scopes=['https://www.googleapis.com/auth/calendar.readonly'],
    redirect_uri='http://localhost:5000/login'  # Redirect to login after Google authorization
)

# Function to get Google Calendar URL
def get_google_calendar_url(credentials):
    service = build('calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    primary_calendar_id = next((item['id'] for item in calendar_list['items'] if item.get('primary')), None)
    return f"https://calendar.google.com/calendar/embed?src={primary_calendar_id}&mode=WEEK"

# Function to calculate weight based on event duration
def calculate_weight(duration):
    if duration >= timedelta(hours=2):
        return 40
    elif timedelta(hours=1) <= duration < timedelta(hours=2):
        return 25
    elif duration < timedelta(hours=1):
        return 10

# Function to calculate the average score for all events
def calculate_average_score(events):
    total_score = 0
    count = 0
    for event in events:
        start_time = event.get('start', {}).get('dateTime')
        end_time = event.get('end', {}).get('dateTime')
        if start_time and end_time:
            total_score += calculate_weight(datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time))
            count += 1
    return total_score / count if count > 0 else 0

@app.route('/')
def index():
    # Redirect to Google authentication
    authorization_url, state = flow.authorization_url(
        access_type='offline', prompt='select_account'
    )
    return redirect(authorization_url)

@app.route('/login')
def login():
    # Fetch the access code from the request parameters
    access_code = request.args.get('code')
    if not access_code:
        return redirect(url_for('index'))  # Redirect to index if no access code

    # Exchange the access code for credentials
    flow.fetch_token(code=access_code)

    # Redirect to onboarding
    return redirect(url_for('onboarding'))

@app.route('/onboarding')
def onboarding():
    # Render the onboarding page
    return render_template('onboarding.html')

@app.route('/dashboard')
def dashboard():
    # Get credentials
    credentials = flow.credentials
    
    # Get Google Calendar events for the current week
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
