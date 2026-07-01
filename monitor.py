import os
import json
import urllib.request
import urllib.error

def send_slack_alert(webhook_url, site_url, error_message):
    payload = {
        "text": f"🚨 *Healthcheck Alert:* Website <{site_url}> appears to be DOWN.\n*Reason:* {error_message}"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        webhook_url, 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                print(f"Failed to send Slack alert. Slack API returned code: {response.status}")
    except Exception as e:
        print(f"Error connecting to Slack Webhook: {e}")

def check_site():
    site_url = os.environ.get("MONITORED_URL")
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not site_url or not webhook_url:
        print("Missing required environment variables.")
        exit(1)

    try:
        # Send request with a standard User-Agent to avoid generic bot-blocking firewalls
        req = urllib.request.Request(
            site_url, 
            headers={'User-Agent': 'GitHub-Actions-Healthcheck-Monitor/1.0'}
        )
        # 10-second timeout ensures the script catches a frozen or hanging server
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            if status == 200:
                print(f"✅ Success! {site_url} is up and running (HTTP 200).")
                exit(0)
            else:
                error_msg = f"Returned unexpected HTTP Status Code {status}"
    
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        error_msg = f"Network Connection/DNS Error: {e.reason}"
    except Exception as e:
        error_msg = f"Unexpected Exception: {str(e)}"

    print(f"❌ {error_msg}")
    send_slack_alert(webhook_url, site_url, error_msg)
    exit(1) # Mark the GitHub Action job as failed

if __name__ == "__main__":
    check_site()
