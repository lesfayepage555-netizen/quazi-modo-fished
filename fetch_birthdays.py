#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import json
import urllib.request
import urllib.error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get environment variables
api_key = os.getenv("YALIES_API_KEY")
if not api_key:
    print("Error: YALIES_API_KEY environment variable not set")
    sys.exit(1)

sender_email = os.getenv("SENDER_EMAIL")
email_password = os.getenv("EMAIL_PASSWORD")
recipient_email = os.getenv("RECIPIENT_EMAIL")

if not sender_email or not email_password or not recipient_email:
    print("Error: SENDER_EMAIL, EMAIL_PASSWORD, and RECIPIENT_EMAIL environment variables must be set")
    sys.exit(1)

# Get today's date
today = datetime.now()
current_month = today.month
current_day = today.day
date_string = today.strftime("%m-%d")

# Prepare headers and request body
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

body = {
    "filters": {
        "birth_month": str(current_month),
        "birth_day": str(current_day),
    },
    "page_size": 100,
}

# Make the API request
try:
    req = urllib.request.Request(
        "https://api.yalies.io/v2/people",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
except urllib.error.URLError as e:
    print(f"Error making API request: {e}")
    sys.exit(1)
except json.JSONDecodeError:
    print("Error: Unable to parse API response as JSON")
    sys.exit(1)

# Extract emails
emails = []
if isinstance(data, list):
    for person in data:
        if "email" in person and person["email"]:
            emails.append(person["email"])
elif isinstance(data, dict) and "data" in data:
    for person in data["data"]:
        if "email" in person and person["email"]:
            emails.append(person["email"])

# Write emails to file
filename = f"emails-{date_string}.txt"
with open(filename, "w") as f:
    for email in emails:
        f.write(email + "\n")

print(f"Found {len(emails)} birthday(s) today")
if emails:
    print(f"Emails saved to {filename}")
    for email in emails:
        print(email)

    # Send email with birthday list
    email_list = "\n".join(emails)

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = f"Birthday Reminders - {date_string}"

    body = f"""
Birthday(s) today ({date_string}):

{email_list}
"""

    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail SMTP server with TLS encryption
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Encrypt the connection
        server.login(sender_email, email_password)
        server.send_message(msg)
        server.quit()

        print(f"\nEmail sent successfully to {recipient_email}")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        sys.exit(1)
else:
    print("No birthdays today")
