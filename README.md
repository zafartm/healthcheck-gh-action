# healthcheck-gh-action
A GitHub action to check the liveness of web apps based upon provided health check url.

---

# Usage

### 1. Create a webhook url in slack
Follow instructions on [https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) to create a webhook URL.

This essentially involves creating a slack app, then enabling webhooks for it. If you already have an app in slack, you can reuse that.

Each webhook is connected with a slack channel. Once configured, the healthcheck action will start sending notifications to that slack channel.

### 2. Create action secret in GitHub - SLACK_WEBHOOK_URL
In the source code repo where you want to run the action, open GitHub settings and create an action secret there. 

Name it SLACK_WEBHOOK_URL. Its value should be the webhook url created above.

### 3. Create a workflow that runs periodically
In the same source code repo where secret is created, create a file in `main` ( or `master`) branch and name it `.github/workflows/healthcheck.yaml`.

Example content of it could be this;
```yaml
name: Scheduled Healthcheck Example
on:
  schedule:
    - cron: "15 * * * *"  # Standard cron expression
  workflow_dispatch: # Allows manual trigger
permissions:
  actions: read   # Needed for 'gh run list
jobs:
  check-website:
    runs-on: ubuntu-latest
    steps:
      - name: Execute Healthcheck
        uses: zafartm/healthcheck-gh-action@main
        with:
          website-url: "https://yahoo.com"
          slack-webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
```
Do not forget to edit website-url. It should point to the webpage that you need to monitor.

You may also want to change the cron expression to match your needs. Min interval that GitHub allows is 5 minutes.

### 4. Test the workflow
Commit and push the workflow file to GitHub.

Go to Actions tab in the repo's web interface. It should be listing a workflow named "Scheduled Healthcheck Example".

Click on the workflow name then run it manually. If things are set up correctly, it should check for the 
health of the provided website url and exit gracefully.

If cron expression in the schedule is defined correctly, GitHub should start repeaing the same action at defined intervals.

---
### Extra notes
Though it is recommended to create the healthcheck workflow in the same GitHub repo where source code of the target server is hosted, but, it is not a strict requirement.
You may create the workflow in any GitHub repo you want and start monitoring any other website. 

It is also possible to monitor multiple webpages in a single workflow. To do so, provide a comma separated list of urls as value to `website-url` property.
