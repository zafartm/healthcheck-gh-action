import os
import sys
import subprocess
import json
import urllib.request
import urllib.error
import time


def main():
    site_urls = os.environ.get("WEBSITE_URL", "").strip().split(",")
    state = get_previous_state()
    print(f"Last saved state: {state}")
    if state is None:
        state = {}
    for site_url in site_urls:
        status = check_site(site_url, state.get(site_url))
        state.update({site_url: {
            "status": status,
            "ts": int(time.time()),
        }})
    print(f"Done checking website urls: {site_urls}")
    print(f"{len(site_urls)} sites checked")
    save_current_state(state)


def check_site(site_url: str, last_state: dict):
    error_msg = None
    status = None
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
                if last_state and last_state.get("status") != 200:
                    send_slack_success(site_url)
            else:
                error_msg = f"Returned unexpected HTTP Status Code {status}"

    except urllib.error.HTTPError as e:
        error_msg = f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        error_msg = f"Network Connection/DNS Error: {e.reason}"
    except Exception as e:
        error_msg = f"Unexpected Exception: {str(e)}"

    if error_msg:
        print(f"❌ {error_msg}")
        if last_state is None or last_state.get("status") != status:
            send_slack_error(site_url, error_msg)

    return status


def send_slack_success(site_url):
    message = f"*Healthcheck Alert:* Website <{site_url}> is ONLINE now."
    send_slack_alert(message)


def send_slack_error(site_url, error_message):
    message = f"🚨 *Healthcheck Alert:* Website <{site_url}> appears to be DOWN.\n*Reason:* {error_message}"
    send_slack_alert(message)


def send_slack_alert(message: str):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    payload = {
        "text": message
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


def get_state_file_name():
    workflow_name = os.getenv("GITHUB_WORKFLOW")
    if not workflow_name:
        print("Error: GITHUB_WORKFLOW env variable not set. Are you running in GitHub Actions?", file=sys.stderr)
    # state_file_name = f"{workflow_name}-state.json"
    state_file_name = os.getenv("STATE_FILE_NAME")
    return state_file_name, workflow_name


def get_previous_state():
    """
    Finds the last successful workflow run using 'gh run list',
    downloads state artifact, and returns its contents as a dict.
    Returns None if no previous state exists.
    """
    # 1. Get the current workflow name from GitHub environment variables
    state_file_name, workflow_name = get_state_file_name()
    try:
        # Query using gh cli for the last successful run ID of this specific workflow
        # gh run list --workflow="Workflow Name" --status=success --limit=1 --json=databaseId
        cmd_list = [
            "gh", "run", "list",
            f"--workflow='{workflow_name}'",
            "--status=success",
            "--limit=1",
            "--json=databaseId"
        ]

        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        runs_data = json.loads(result.stdout)

        if not runs_data:
            print("No previous successful workflow runs found. Starting fresh.")
            return None

        last_run_id = str(runs_data[0]["databaseId"])
        print(f"Found last successful run ID: {last_run_id}")

        cmd_download = [
            "gh", "run", "download", last_run_id, "--name", state_file_name
        ]

        # We catch the error here in case the run was successful but had no artifact
        download_result = subprocess.run(cmd_download, capture_output=True, text=True)

        if download_result.returncode != 0:
            print(f"No state artifact found for run ID {last_run_id}. Starting fresh.")
            return None
        else:
            with open(state_file_name, "r") as f:
                return json.load(f)

    except Exception as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        return None


def save_current_state(state: dict):
    """
    Saves the dictionary locally to the state file in json format.
    The actual artifact uploading step must be done in your YAML file
    using actions/upload-artifact, as 'gh' CLI cannot upload new run artifacts natively.
    """
    try:
        state_file_name, workflow_name = get_state_file_name()
        with open(state_file_name, "w") as f:
            json.dump(state, f, indent=2)
        print(f"Successfully saved updated state locally to {state_file_name}")
    except Exception as e:
        print(f"Error saving state to file: {e}")


if __name__ == "__main__":
    main()
