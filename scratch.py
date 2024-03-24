from flask import Flask, render_template, redirect, url_for, request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta


app = Flask(__name__)

# Function to get Google Calendar URL
def get_google_calendar_url(credentials):
    service = build('calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    primary_calendar_id = next((item['id'] for item in calendar_list['items'] if item.get('primary')), None)
    return f"https://calendar.google.com/calendar/embed?src={primary_calendar_id}"

# Define the flow globally
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret_131606957380-u4ikuhues6u5s60dtueah3mgncn9u2u1.apps.googleusercontent.com.json', 
    scopes=['https://www.googleapis.com/auth/calendar.readonly'],
    redirect_uri='http://localhost:5000/dashboard'  # Ensure this matches your redirect URI
)

def sort_events(primary_calendar_id):
    small = {'quantity': 0, 'score': 0}
    medium = {'quantity': 0, 'score': 0}
    large = {'quantity': 0, 'score': 0}
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Get the start of the week (Monday)
    end_of_week = start_of_week + timedelta(days=7)  # Get the end of the week (Sunday)

    for event in primary_calendar_id:
        start_time_str = event['start'].get('dateTime', event['start'].get('date'))
        start_time = datetime.fromisoformat(start_time_str)
        
        # Check if the event is within the present week
        if start_time >= start_of_week and start_time < end_of_week:
            end_time_str = event['end'].get('dateTime', event['end'].get('date'))
            
            # Parse start and end time strings into datetime objects
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)

            # Calculate the duration in minutes
            duration_minutes = (end_time - start_time).total_seconds() / 60

        if duration_minutes < 60:
            small['quantity'] = small['quantity'] + 1
            small['score'] = small['score'] + 10
        elif duration_minutes < 120:
            medium['quantity'] = medium['quantity'] + 1
            medium['score'] = medium['score'] + 25
        else:
            large['quantity'] = large['quantity'] + 1
            large['score'] = large['score'] + 40
    
    return (small['score']+medium['score']+large['score'])/(small['quantity']+medium['quantity']+large['quantity'])



# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url(
        access_type='offline', prompt='select_account'
    )
    return redirect(authorization_url)

@app.route('/dashboard')
def dashboard():
    # Fetch the access code from the request parameters
    access_code = request.args.get('code')

    # Exchange the access code for credentials
    flow.fetch_token(code=access_code)

    # Get Google Calendar URL
    credentials = flow.credentials
    google_calendar_url = get_google_calendar_url(credentials)

    battery = sort_events(google_calendar_url)

    return render_template('dashboard.html', google_calendar_url=google_calendar_url)

if __name__ == '__main__':
    app.run(debug=True)