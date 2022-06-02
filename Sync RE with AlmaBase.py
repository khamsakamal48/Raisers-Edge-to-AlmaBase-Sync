#!/usr/bin/env python3

import requests, os, json, glob, csv, psycopg2, sys

# Set current directory
#os.chdir(os.path.dirname(sys.argv[0]))
os.chdir(os.getcwd())

from dotenv import load_dotenv

load_dotenv()

# Retrieve contents from .env file
DB_IP = os.getenv("DB_IP")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
RE_API_KEY = os.getenv("RE_API_KEY")
MAIL_USERN = os.getenv("MAIL_USERN")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
IMAP_URL = os.getenv("IMAP_URL")
IMAP_PORT = os.getenv("IMAP_PORT")
SMTP_URL = os.getenv("SMTP_URL")
SMTP_PORT = os.getenv("SMTP_PORT")
SEND_TO  = os.getenv("SEND_TO")
ALMABASE_API_KEY = os.getenv("ALMABASE_API_KEY")
ALMABASE_API_TOKEN = os.getenv("ALMABASE_API_TOKEN")

# Retrieve access_token from file
with open('access_token_output.json') as access_token_output:
  data = json.load(access_token_output)
  access_token = data["access_token"]

def get_request_re():
    # Request Headers for Blackbaud API request
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    }
    
    global api_response
    api_response = requests.get(url, params=params, headers=headers).json()
    
    check_for_errors()
  
def post_request_re():
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json',
    }
    
    global api_response
    api_response = requests.post(url, params=params, headers=headers, json=params).json()
    
    check_for_errors()

def patch_request_re():
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
    }
    
    global api_response
    api_response = requests.patch(url, headers=headers, data=params)
    
    check_for_errors()
    
def check_for_errors():
    error_keywords = ["invalid", "error", "bad", "Unauthorized", "Forbidden", "Not Found", "Unsupported Media Type", "Too Many Requests", "Internal Server Error", "Service Unavailable", "Unexpected", "error_code", "400"]
    
    if any(x in api_response for x in error_keywords):
        # Send emails
        print ("Will send email now")
        send_error_emails()

def send_error_emails():
    print ("Calling function Send error emails")
    print (api_response)
    # message = MIMEMultipart("alternative")
    # message["Subject"] = "Unable to find Alum in Raisers Edge for Stay Connected"
    # message["From"] = MAIL_USERN
    # message["To"] = MAIL_USERN

    # # Adding Reply-to header
    # message.add_header('reply-to', MAIL_USERN)
        
    # TEMPLATE="""
    # <table style="background-color: #ffffff; border-color: #ffffff; width: auto; margin-left: auto; margin-right: auto;">
    # <tbody>
    # <tr style="height: 127px;">
    # <td style="background-color: #363636; width: 100%; text-align: center; vertical-align: middle; height: 127px;">&nbsp;
    # <h1><span style="color: #ffffff;">&nbsp;Raiser's Edge Automation: {job_name} Failed</span>&nbsp;</h1>
    # </td>
    # </tr>
    # <tr style="height: 18px;">
    # <td style="height: 18px; background-color: #ffffff; border-color: #ffffff;">&nbsp;</td>
    # </tr>
    # <tr style="height: 18px;">
    # <td style="width: 100%; height: 18px; background-color: #ffffff; border-color: #ffffff; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #455362;">This is to notify you that execution of Auto-updating Alumni records has failed.</span>&nbsp;</td>
    # </tr>
    # <tr style="height: 18px;">
    # <td style="height: 18px; background-color: #ffffff; border-color: #ffffff;">&nbsp;</td>
    # </tr>
    # <tr style="height: 61px;">
    # <td style="width: 100%; background-color: #2f2f2f; height: 61px; text-align: center; vertical-align: middle;">
    # <h2><span style="color: #ffffff;">Job details:</span></h2>
    # </td>
    # </tr>
    # <tr style="height: 52px;">
    # <td style="height: 52px;">
    # <table style="background-color: #2f2f2f; width: 100%; margin-left: auto; margin-right: auto; height: 42px;">
    # <tbody>
    # <tr>
    # <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Job :</span>&nbsp;</td>
    # <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{job_name}&nbsp;</td>
    # </tr>
    # <tr>
    # <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Failed on :</span>&nbsp;</td>
    # <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{current_time}&nbsp;</td>
    # </tr>
    # </tbody>
    # </table>
    # </td>
    # </tr>
    # <tr style="height: 18px;">
    # <td style="height: 18px; background-color: #ffffff;">&nbsp;</td>
    # </tr>
    # <tr style="height: 18px;">
    # <td style="height: 18px; width: 100%; background-color: #ffffff; text-align: center; vertical-align: middle;">Below is the detailed error log,</td>
    # </tr>
    # <tr style="height: 217.34375px;">
    # <td style="height: 217.34375px; background-color: #f8f9f9; width: 100%; text-align: left; vertical-align: middle;">{error_log_message}</td>
    # </tr>
    # </tbody>
    # </table>
    # """
    
    # # Create a text/html message from a rendered template
    # emailbody = MIMEText(
    # Environment().from_string(TEMPLATE).render(
    #     job_name="Updates from Stay Connected",
    #     error_log_message=api_response,
    #     current_time=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    #     ), "html"
    # )
    
    # # Add HTML parts to MIMEMultipart message
    # # The email client will try to render the last part first
    # message.attach(emailbody)
    # emailcontent = message.as_string()

    # # Create secure connection with server and send email
    # context = ssl._create_unverified_context()
    # with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
    #     server.login(MAIL_USERN, MAIL_PASSWORD)
    #     server.sendmail(
    #         MAIL_USERN, MAIL_USERN, emailcontent
    #     )

    # # Save copy of the sent email to sent items folder
    # with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
    #     imap.login(MAIL_USERN, MAIL_PASSWORD)
    #     imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
    #     imap.logout()

    # Close DB connection
    cur.close()
    conn.close()

    sys.exit()

# PostgreSQL DB Connection
conn = psycopg2.connect(host=DB_IP, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

# Open connection
cur = conn.cursor()

# Query the next data to uploaded in RE
extract_sql = """
        SELECT system_id FROM all_alums_in_re EXCEPT SELECT system_id FROM alread_synced FETCH FIRST 1 ROW ONLY;
        """
cur.execute(extract_sql)
result = cur.fetchone()

# Ensure no comma or brackets in output
re_system_id = result[0]

# Get email list
url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/emailaddresses" % re_system_id

# Blackbaud API GET request
get_request_re()