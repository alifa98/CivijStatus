import os
import requests
import json
import base64
from datetime import datetime

TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

GITHUB_REPO = "alifa98/CivijStatus"
GITHUB_TOKEN = os.getenv('GH_TOKEN')

def check_website(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200, response.elapsed.total_seconds()
    except requests.RequestException:
        return False, None

def notify_telegram(message):
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    requests.post(TELEGRAM_API_URL, data=data)

def update_github_log(log_content):
    # Prepare GitHub API URL
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/uptime_log.csv"

    # Get current timestamp (UTC)
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Get the latest file details
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        # If file exists, get its SHA
        file_data = response.json()
        sha = file_data['sha']
        current_content = base64.b64decode(file_data['content']).decode()
        new_content = f"{current_content}\n{log_content}"
    else:
        # If file doesn't exist, create new content
        sha = None
        new_content = log_content

    # Encode the content to base64
    encoded_content = base64.b64encode(new_content.encode()).decode()

    # Prepare the request payload
    payload = {
        "message": f"Updated uptime log at {current_time}",
        "content": encoded_content,
    }
    if sha:
        payload["sha"] = sha

    # Send a PUT request to update the file on GitHub
    response = requests.put(api_url, headers=headers, data=json.dumps(payload))
    return response.status_code == 200

# List of websites to check
websites = ["https://app.civij.com", "https://civij.com"]
for website in websites:
    status, response_time = check_website(website)
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if not status:
        notify_telegram(f"Website {website} is down as of {current_time} (UTC)!")
    
    # Log the status (True/False) and response time
    log_content = f"{current_time},{website},{status},{response_time}"
    
    # Update the log in the GitHub repository
    update_github_log(log_content)
