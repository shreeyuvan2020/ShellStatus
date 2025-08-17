import requests
from bs4 import BeautifulSoup
import secrets
import os
import json
from flask import Flask, render_template, request, redirect, session
url = "https://summer.hackclub.com/campfire"
redirect_uri = "https://starchecker.tech/slack_redirect"
client_id = "2210535565.9204097075860"
client_secret = os.getenv("ShellSecret")
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
def set_slack_status(access_token, cookies):
    url = "https://summer.hackclub.com/campfire"
    response = requests.get(url, cookies=cookies)
    soup = BeautifulSoup(response.text, 'html.parser')
    print(soup.prettify())
    shell_count = soup.find("span", class_="ml-1")
    print(shell_count.text.strip())
    headers = {"Content-type": "application/json; charset=utf-8", "Authorization": f"Bearer {access_token}"}
    payload = {"profile": {"status_text": shell_count.text.strip() + " shells", "status_emoji": ":shells:", "status_expiration": 0}}
    response = requests.post("https://slack.com/api/users.profile.set", headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())
@app.route('/', methods=["GET"])
def index():
    return render_template('index.html')
@app.route('/set_cookie', methods=['POST'])
def set_cookie():
    cookie_value = request.form.get('cookie_value')
    if not cookie_value:
        return "No cookie value provided", 400
    # Save the cookie value to a file
    session['cookie_value'] = cookie_value
    return redirect('/login')
@app.route('/login')
def login():
    state = secrets.token_urlsafe(32) # Wow such secure idk why slack needs it but they do
    print(f"State: {state}")
    session['state'] = state # putting it into the flask session so i can access it later
    scopes = "users.profile:write" # need this scope to set status
    auth_url = f"https://slack.com/oauth/v2/authorize?"f"client_id={client_id}&client_secret={client_secret}&user_scope={scopes}&state={state}&redirect_uri={redirect_uri}"
    return redirect(auth_url)
@app.route('/slack_redirect') # redirects me to slack wow nobody knew that for sure right
def slack_redirect():
    print("Redirecting to Slack...")
    access_url = "https://slack.com/api/oauth.v2.access" #url to exchange code for access token
    if request.args.get('state') != session['state']:
        return "State does not match, possible CSRF attack", 403 # oh no me scared
    code = request.args.get('code')
    print(client_id)
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri
    } # payload to send to slack to get access token
    response = requests.post(access_url, data=payload)
    print(response.text)
    if response.status_code == 200 and response.json().get('ok'):
        access_token = response.json().get('authed_user').get('access_token')
        session['access_token'] = access_token
        print(response.json())
        return redirect('/set_status')
    else:
        print("Error:", response.json())
        return "It failed, check the logs for more info"
@app.route('/set_status')
def set_status():
    set_slack_status(session['access_token'], {"_journey_session": session['cookie_value']})
    return render_template('success.html')
