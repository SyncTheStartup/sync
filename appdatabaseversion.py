from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"

conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                scheduling TEXT,
                mental_health TEXT,
                large_parties TEXT
            )''')
conn.commit()

# Define the flow globally
flow = Flow.from_client_secrets_file(
    'client_secret_131606957380-ps44nt6hrpul20q162mke20i1e260kv4.apps.googleusercontent.com.json', 
    scopes=['https://www.googleapis.com/auth/calendar.readonly'],
    redirect_uri='http://localhost:5000/login'  # Redirect to login after Google authorization
)

# Function to get Google Calendar URL
def get_google_calendar_url(credentials):
    service = build('calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    primary_calendar_id = next((item['id'] for item in calendar_list['items'] if item.get('primary')), None)
    return f"https://calendar.google.com/calendar/embed?src={primary_calendar_id}&mode=WEEK"

@app.route('/')
def index():
    # Generate a unique state parameter
    state = str(uuid.uuid4())
    session['state'] = state

    print("index state:", session['state'])
    # Redirect to Google authentication with the state parameter
    authorization_url, _ = flow.authorization_url(
        state=state,
        access_type='offline',
        prompt='select_account'
    )
    return redirect(authorization_url)

@app.route('/login')
def login():
    # Check if the states match
    # print("request args: " , request.args.get('state'))
    # print("session pop:", session.pop('state', None))
    print("session without pop", session)
    # if request.args.get('state') != session.pop('state', None):
    #     return 'Invalid state parameter', 400

    # Exchange the authorization code for credentials
    flow.fetch_token(code=request.args.get('code'))
    
    # Store credentials in session
    session['credentials'] = flow.credentials.to_json()

    # Redirect to onboarding
    return redirect(url_for('onboarding'))

# Function to decode ID token and get email
def get_email_from_credentials(credentials):
    decoded_token = credentials['id_token']
    token_data = json.loads(decoded_token)
    return token_data['email']

@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    # Retrieve credentials from session
    credentials_json = session.get('credentials')
    if not credentials_json:
        return redirect(url_for('index'))  # Redirect to index if no credentials

    # Convert credentials JSON to object
    credentials = json.loads(credentials_json)

    if request.method == 'POST':
        email = get_email_from_credentials(credentials)
        scheduling = request.form['scheduling']
        mental_health = request.form['mentalHealth']
        large_parties = request.form['largeParties']

        # Insert data into the database
        c.execute('INSERT INTO users (email, scheduling, mental_health, large_parties) VALUES (?, ?, ?, ?)',
                  (email, scheduling, mental_health, large_parties))
        conn.commit()

        return redirect(url_for('dashboard'))

    return render_template('onboarding.html')


@app.route('/dashboard')
def dashboard():
    # Get credentials from session
    credentials_json = session.get('credentials')
    if not credentials_json:
        return redirect(url_for('index'))  # Redirect to index if no credentials

    # Convert credentials JSON to object
    credentials = json.loads(credentials_json)

    # Get Google Calendar URL
    google_calendar_url = get_google_calendar_url(credentials)

    return render_template('dashboard.html', google_calendar_url=google_calendar_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)