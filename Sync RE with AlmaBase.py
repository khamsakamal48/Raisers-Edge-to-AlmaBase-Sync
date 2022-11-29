#!/usr/bin/env python3

from cmath import e
from sqlite3 import paramstyle
from textwrap import indent
from click import echo
import requests, os, json, glob, csv, psycopg2, sys, smtplib, ssl, imaplib, time, email, re, fuzzywuzzy, itertools, geopy, datetime, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from jinja2 import Environment
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# Printing the output to file for debugging
sys.stdout = open('Process.log', 'w')

# API Request strategy
print("Setting API Request strategy")
retry_strategy = Retry(
total=3,
status_forcelist=[429, 500, 502, 503, 504],
allowed_methods=["HEAD", "GET", "OPTIONS"],
backoff_factor=10
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# Set current directory
print("Setting current directory")
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

# PostgreSQL DB Connection
conn = psycopg2.connect(host=DB_IP, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

# Open connection
print("Creating connection with SQL database")
cur = conn.cursor()

# Retrieve access_token from file
print("Retrieve token from API connections")
with open('access_token_output.json') as access_token_output:
    data = json.load(access_token_output)
    access_token = data["access_token"]

def get_request_re():
    print("Running GET Request from RE function")
    time.sleep(5)
    # Request Headers for Blackbaud API request
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    }
    
    global re_api_response
    re_api_response = http.get(url, params=params, headers=headers).json()
    
    check_for_errors()

def get_request_almabase():
    print("Running GET Request from Almabase function")
    time.sleep(5)
    # Request Headers for AlmaBase API request
    headers = {
        "User-Agent":"Mozilla/5.0",
        'Accept': 'application/json',
        'X-API-Access-Key': ALMABASE_API_KEY,
        'X-API-Access-Token': ALMABASE_API_TOKEN,
    }
    
    global ab_api_response
    ab_api_response = http.get(url, headers=headers).json()
    
    print_json(ab_api_response)
    
    check_for_errors()

def post_request_re():
    print("Running POST Request to RE function")
    time.sleep(5)
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json',
    }
    
    global re_api_response
    re_api_response = http.post(url, params=params, headers=headers, json=params).json()
    
    check_for_errors()

def patch_request_re():
    print("Running PATCH Request to RE function")
    time.sleep(5)
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
    }
    
    global re_api_response
    re_api_response = http.patch(url, headers=headers, data=json.dumps(params))
    
    check_for_errors()
    
def patch_request_ab():
    print("Running PATCH Request to Almabase function")
    time.sleep(5)
    # Request Headers for AlmaBase API request
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-Access-Key': ALMABASE_API_KEY,
        'X-API-Access-Token': ALMABASE_API_TOKEN,
    }
    
    global ab_api_response
    ab_api_response = http.patch(url, headers=headers, json=params)
    
    check_for_errors()

def post_request_ab():
    print("Running POST Request from Almabase function")
    time.sleep(5)
    # Request Headers for AlmaBase API request
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-Access-Key': ALMABASE_API_KEY,
        'X-API-Access-Token': ALMABASE_API_TOKEN,
    }
    
    global ab_api_response
    ab_api_response = http.post(url, headers=headers, json=params)
    
    check_for_errors()
    
def check_for_errors():
    print("Checking for errors")
    
    global subject
    
    error_keywords = ["invalid", "error", "bad", "Unauthorized", "Forbidden", "Not Found", "Unsupported Media Type", "Too Many Requests", "Internal Server Error", "Service Unavailable", "Unexpected", "error_code", "400"]
    
    if any(x in re_api_response for x in error_keywords):
        # Send emails
        subject = 'Error while syncing Raisers Edge and Almabase'
        print ("Will send email now")
        print(subject)
        send_error_emails()
        
    try:
        error_name = re_api_response[0]['error_name']
        
        if error_name == 'ContactBusinessLogicPhoneNumberIsInvalid':
            # Send emails
            print ("Will send email now")
            subject = 'Error while syncing Raisers Edge and Almabase: Phone Number is invalid'
            print(subject)
            send_error_emails()
    except:
        pass
        

def attach_file_to_email(message, filename):
    # Open the attachment file for reading in binary mode, and make it a MIMEApplication class
    with open(filename, "rb") as f:
        file_attachment = MIMEApplication(f.read())
    # Add header/name to the attachments    
    file_attachment.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )
    # Attach the file to the message
    message.attach(file_attachment)

def send_error_emails():
    print("Sending email for an error")
    
    try:
        if sys.stdout:
            sys.stdout.close()
            
    except:
        pass

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = MAIL_USERN
    message["To"] = SEND_TO

    # Adding Reply-to header
    message.add_header('reply-to', MAIL_USERN)
        
    TEMPLATE="""
    <table style="background-color: #ffffff; border-color: #ffffff; width: auto; margin-left: auto; margin-right: auto;">
    <tbody>
    <tr style="height: 127px;">
    <td style="background-color: #363636; width: 100%; text-align: center; vertical-align: middle; height: 127px;">&nbsp;
    <h1><span style="color: #ffffff;">&nbsp;Raiser's Edge Automation: {{job_name}} Failed</span>&nbsp;</h1>
    </td>
    </tr>
    <tr style="height: 18px;">
    <td style="height: 18px; background-color: #ffffff; border-color: #ffffff;">&nbsp;</td>
    </tr>
    <tr style="height: 18px;">
    <td style="width: 100%; height: 18px; background-color: #ffffff; border-color: #ffffff; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #455362;">This is to notify you that execution of Auto-updating Alumni records has failed.</span>&nbsp;</td>
    </tr>
    <tr style="height: 18px;">
    <td style="height: 18px; background-color: #ffffff; border-color: #ffffff;">&nbsp;</td>
    </tr>
    <tr style="height: 61px;">
    <td style="width: 100%; background-color: #2f2f2f; height: 61px; text-align: center; vertical-align: middle;">
    <h2><span style="color: #ffffff;">Job details:</span></h2>
    </td>
    </tr>
    <tr style="height: 52px;">
    <td style="height: 52px;">
    <table style="background-color: #2f2f2f; width: 100%; margin-left: auto; margin-right: auto; height: 42px;">
    <tbody>
    <tr>
    <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Job :</span>&nbsp;</td>
    <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{{job_name}}&nbsp;</td>
    </tr>
    <tr>
    <td style="width: 50%; text-align: center; vertical-align: middle;">&nbsp;<span style="color: #ffffff;">Failed on :</span>&nbsp;</td>
    <td style="background-color: #ff8e2d; width: 50%; text-align: center; vertical-align: middle;">&nbsp;{{current_time}}&nbsp;</td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    <tr style="height: 18px;">
    <td style="height: 18px; background-color: #ffffff;">&nbsp;</td>
    </tr>
    <tr style="height: 18px;">
    <td style="height: 18px; width: 100%; background-color: #ffffff; text-align: center; vertical-align: middle;">Below is the detailed error log,</td>
    </tr>
    <tr style="height: 217.34375px;">
    <td style="height: 217.34375px; background-color: #f8f9f9; width: 100%; text-align: left; vertical-align: middle;">{{error_log_message}}</td>
    </tr>
    </tbody>
    </table>
    """

    # Create a text/html message from a rendered template
    emailbody = MIMEText(
        Environment().from_string(TEMPLATE).render(
            job_name = "Syncing Raisers Edge and AlmaBase",
            current_time=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            error_log_message = Argument
        ), "html"
    )

    # Add HTML parts to MIMEMultipart message
    # The email client will try to render the last part first
    try:
        message.attach(emailbody)
        attach_file_to_email(message, 'Process.log')
        emailcontent = message.as_string()
        
    except:
        message.attach(emailbody)
        emailcontent = message.as_string()
    
    # Create secure connection with server and send email
    context = ssl._create_unverified_context()
    with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
        server.login(MAIL_USERN, MAIL_PASSWORD)
        server.sendmail(
            MAIL_USERN, SEND_TO, emailcontent
        )

    # Save copy of the sent email to sent items folder
    with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
        imap.login(MAIL_USERN, MAIL_PASSWORD)
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
        imap.logout()

def notify_sync_finished():
    print("Notifying that Sync has finished")
    
    subject = "Raisers Edge & Almabase Sync has finished"
    
    # # Close writing to Process.log
    # sys.stdout.close()
    
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = MAIL_USERN
    message["To"] = SEND_TO
    
    # Adding Reply-to header
    message.add_header('reply-to', MAIL_USERN)
    
    TEMPLATE = """
    <html>
        <body>
            <p>Hi,<br><br>
            This is to inform you that the Raisers Edge <-> Almabase syncing has finished for all the Alums assisgned to the list.<br><br>
            The program will re-start the sync from start and make updates in the records on the go.<br><br>
            This if for your information and requires no further action from your end.<br><br><br>
            Thanks & Regards<br>
            a BOT<br>
            </p>
        </body>
    </html>
    """
    
    # Create a text/html message from a rendered template
    emailbody = MIMEText(
        Environment().from_string(TEMPLATE).render(), "html"
    )
    
    # Add HTML parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(emailbody)
    emailcontent = message.as_string()
    
    # Create secure connection with server and send email
    context = ssl._create_unverified_context()
    with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
        server.login(MAIL_USERN, MAIL_PASSWORD)
        server.sendmail(
            MAIL_USERN, SEND_TO, emailcontent
        )

    # Save copy of the sent email to sent items folder
    with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
        imap.login(MAIL_USERN, MAIL_PASSWORD)
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
        imap.logout()
        
    # Close DB connection
    if conn:
        cur.close()
        conn.close()
        
    exit()
    
def multiple_education_exists():
    print("Notifying that Multiple IITB Education exists")
    
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = MAIL_USERN
    message["To"] = SEND_TO
    
    # Adding Reply-to header
    message.add_header('reply-to', MAIL_USERN)
    
    TEMPLATE = """
    <html>
        <body>
            <p>Hi,<br><br>
            This is to inform you that Multiple IIT Bombay education exists while performing Raisers Edge <-> Almabase sync and hence couldn't update their IITB Education records.<br><br>
            Requesting you the please check the same in RE and Almabase and update (if required).<br><br>
            Education details:<br><br>
            Raisers Edge:<br><br>
            System ID: {{re_system_id}}<br><br>
            {{re_api_response_education}}<br><br><br>
            Almabase:<br><br>
            {{ab_api_response_education}}
            <br><br><br>
            Thanks & Regards<br>
            a BOT<br>
            </p>
        </body>
    </html>
    """
    
    # Create a text/html message from a rendered template
    emailbody = MIMEText(
        Environment().from_string(TEMPLATE).render(
            re_system_id=re_system_id,
            re_api_response_education=re_api_response_education,
            ab_api_response_education=ab_api_response_education
            ), "html"
    )
    
    # Add HTML parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(emailbody)
    emailcontent = message.as_string()
    
    # Create secure connection with server and send email
    context = ssl._create_unverified_context()
    with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
        server.login(MAIL_USERN, MAIL_PASSWORD)
        server.sendmail(
            MAIL_USERN, SEND_TO, emailcontent
        )

    # Save copy of the sent email to sent items folder
    with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
        imap.login(MAIL_USERN, MAIL_PASSWORD)
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
        imap.logout()

def constituent_not_found_email():
    print("Sending an email that the constituent wasn't found")
    
    # Checking if it's evening to avoid sending emails
    current_time = time.strftime("%H", time.localtime())
    
    if 10 <= int(current_time) < 19:
    
        # Query the next data to uploaded in RE
        extract_sql = """
                SELECT re_system_id FROM all_alums_in_re EXCEPT SELECT re_system_id FROM already_synced FETCH FIRST 1 ROW ONLY;
                """
        cur.execute(extract_sql)
        result = cur.fetchone()

        # Ensure no comma or brackets in output
        re_system_id = result[0]
        
        extract_sql = """
                SELECT name FROM all_alums_in_re where re_system_id = %s;
                """
        
        cur.execute(extract_sql, [re_system_id])
        result = cur.fetchone()
                    
        # Ensure no comma or brackets in output
        name = result[0]
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = MAIL_USERN
        message["To"] = SEND_TO

        # Adding Reply-to header
        message.add_header('reply-to', MAIL_USERN)

        TEMPLATE = """
        <!DOCTYPE html>
        <html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
        <head>
            <meta charset="utf-8"> <!-- utf-8 works for most cases -->
            <meta name="viewport" content="width=device-width"> <!-- Forcing initial-scale shouldn't be necessary -->
            <meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- Use the latest (edge) version of IE rendering engine -->
            <meta name="x-apple-disable-message-reformatting">  <!-- Disable auto-scale in iOS 10 Mail entirely -->
            <title>Create a Donor?</title> <!-- The title tag shows in email notifications, like Android 4.4. -->
            <!-- Web Font / @font-face : BEGIN -->
            <!-- NOTE: If web fonts are not required, lines 10 - 27 can be safely removed. -->
            <!-- Desktop Outlook chokes on web font references and defaults to Times New Roman, so we force a safe fallback font. -->
            <!--[if mso]>
                <style>
                    * {
                        font-family: Arial, sans-serif !important;
                    }
                </style>
            <![endif]-->
            <!-- All other clients get the webfont reference; some will render the font and others will silently fail to the fallbacks. More on that here: http://stylecampaign.com/blog/2015/02/webfont-support-in-email/ -->
            <!--[if !mso]><!-->
                <link href="https://fonts.googleapis.com/css?family=Montserrat:300,500" rel="stylesheet">
            <!--<![endif]-->
            <!-- Web Font / @font-face : END -->
            <!-- CSS Reset -->
            <style>
                /* What it does: Remove spaces around the email design added by some email clients. */
                /* Beware: It can remove the padding / margin and add a background color to the compose a reply window. */
                html,
                body {
                    margin: 0 auto !important;
                    padding: 0 !important;
                    height: 100% !important;
                    width: 100% !important;
                }
                /* What it does: Stops email clients resizing small text. */
                * {
                    -ms-text-size-adjust: 100%;
                    -webkit-text-size-adjust: 100%;
                }
                /* What it does: Centers email on Android 4.4 */
                div[style*="margin: 16px 0"] {
                    margin:0 !important;
                }
                /* What it does: Stops Outlook from adding extra spacing to tables. */
                table,
                td {
                    mso-table-lspace: 0pt !important;
                    mso-table-rspace: 0pt !important;
                }
                /* What it does: Fixes webkit padding issue. Fix for Yahoo mail table alignment bug. Applies table-layout to the first 2 tables then removes for anything nested deeper. */
                table {
                    border-spacing: 0 !important;
                    border-collapse: collapse !important;
                    table-layout: fixed !important;
                    margin: 0 auto !important;
                }
                table table table {
                    table-layout: auto;
                }
                /* What it does: Uses a better rendering method when resizing images in IE. */
                img {
                    -ms-interpolation-mode:bicubic;
                }
                /* What it does: A work-around for email clients meddling in triggered links. */
                *[x-apple-data-detectors],  /* iOS */
                .x-gmail-data-detectors,    /* Gmail */
                .x-gmail-data-detectors *,
                .aBn {
                    border-bottom: 0 !important;
                    cursor: default !important;
                    color: inherit !important;
                    text-decoration: none !important;
                    font-size: inherit !important;
                    font-family: inherit !important;
                    font-weight: inherit !important;
                    line-height: inherit !important;
                }
                /* What it does: Prevents Gmail from displaying an download button on large, non-linked images. */
                .a6S {
                    display: none !important;
                    opacity: 0.01 !important;
                }
                /* If the above doesn't work, add a .g-img class to any image in question. */
                img.g-img + div {
                    display:none !important;
                    }
                /* What it does: Prevents underlining the button text in Windows 10 */
                .button-link {
                    text-decoration: none !important;
                }
                /* What it does: Removes right gutter in Gmail iOS app: https://github.com/TedGoas/Cerberus/issues/89  */
                /* Create one of these media queries for each additional viewport size you'd like to fix */
                /* Thanks to Eric Lepetit @ericlepetitsf) for help troubleshooting */
                @media only screen and (min-device-width: 375px) and (max-device-width: 413px) { /* iPhone 6 and 6+ */
                    .email-container {
                        min-width: 375px !important;
                    }
                }
            </style>
            <!-- Progressive Enhancements -->
            <style>
                /* What it does: Hover styles for buttons */
                .button-td,
                .button-a {
                    transition: all 100ms ease-in;
                }
                .button-td:hover,
                .button-a:hover {
                    background: #555555 !important;
                    border-color: #555555 !important;
                }
                /* Media Queries */
                @media screen and (max-width: 480px) {
                    /* What it does: Forces elements to resize to the full width of their container. Useful for resizing images beyond their max-width. */
                    .fluid {
                        width: 100% !important;
                        max-width: 100% !important;
                        height: auto !important;
                        margin-left: auto !important;
                        margin-right: auto !important;
                    }
                    /* What it does: Forces table cells into full-width rows. */
                    .stack-column,
                    .stack-column-center {
                        display: block !important;
                        width: 100% !important;
                        max-width: 100% !important;
                        direction: ltr !important;
                    }
                    /* And center justify these ones. */
                    .stack-column-center {
                        text-align: center !important;
                    }
                    /* What it does: Generic utility class for centering. Useful for images, buttons, and nested tables. */
                    .center-on-narrow {
                        text-align: center !important;
                        display: block !important;
                        margin-left: auto !important;
                        margin-right: auto !important;
                        float: none !important;
                    }
                    table.center-on-narrow {
                        display: inline-block !important;
                    }
                    /* What it does: Adjust typography on small screens to improve readability */
                    .email-container p {
                        font-size: 17px !important;
                        line-height: 22px !important;
                    }
                }
            </style>
            <!-- What it does: Makes background images in 72ppi Outlook render at correct size. -->
            <!--[if gte mso 9]>
            <xml>
                <o:OfficeDocumentSettings>
                    <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch>
                </o:OfficeDocumentSettings>
            </xml>
            <![endif]-->
        </head>
        <body width="100%" bgcolor="#F1F1F1" style="margin: 0; mso-line-height-rule: exactly;">
            <center style="width: 100%; background: #F1F1F1; text-align: left;">
                <!-- Visually Hidden Preheader Text : BEGIN -->
                <div style="display:none;font-size:1px;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;mso-hide:all;font-family: sans-serif;">
                    Hello Kamal, I couldn't find below donor in Raiser's Edge. Let me know what you want me to do now.
                </div>
                <!-- Visually Hidden Preheader Text : END -->
                <!--
                    Set the email width. Defined in two places:
                    1. max-width for all clients except Desktop Windows Outlook, allowing the email to squish on narrow but never go wider than 680px.
                    2. MSO tags for Desktop Windows Outlook enforce a 680px width.
                    Note: The Fluid and Responsive templates have a different width (600px). The hybrid grid is more "fragile", and I've found that 680px is a good width. Change with caution.
                -->
                <div style="max-width: 680px; margin: auto;" class="email-container">
                    <!--[if mso]>
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="680" align="center">
                    <tr>
                    <td>
                    <![endif]-->
                    <!-- Email Body : BEGIN -->
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 680px;" class="email-container">
                        <!-- HEADER : BEGIN -->
                        <tr>
                            <td bgcolor="#333333">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="padding: 10px 40px 10px 40px; text-align: center;">
                                            <img src="https://i.ibb.co/fk6J37P/iitblogowhite.png" width="57" height="13" alt="alt_text" border="0" style="height: auto; font-family: sans-serif; font-size: 15px; line-height: 20px; color: #555555;">
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- HEADER : END -->
                        <!-- HERO : BEGIN -->
                        <tr>
                            <!-- Bulletproof Background Images c/o https://backgrounds.cm -->
                            <td background="https://i.ibb.co/y8dhxm3/Background.png" bgcolor="#222222" align="center" valign="top" style="text-align: center; background-position: center center !important; background-size: cover !important;">
                                <!--[if gte mso 9]>
                                <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:680px; height:380px; background-position: center center !important;">
                                <v:fill type="tile" src="background.png" color="#222222" />
                                <v:textbox inset="0,0,0,0">
                                <![endif]-->
                                <div>
                                    <!--[if mso]>
                                    <table role="presentation" border="0" cellspacing="0" cellpadding="0" align="center" width="500">
                                    <tr>
                                    <td align="center" valign="middle" width="500">
                                    <![endif]-->
                                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center" width="100%" style="max-width:500px; margin: auto;">
                                        <tr>
                                            <td height="20" style="font-size:20px; line-height:20px;">&nbsp;</td>
                                        </tr>
                                        <tr>
                                            <td align="center" valign="middle">
                                            <table>
                                            <tr>
                                                <td valign="top" style="text-align: center; padding: 60px 0 10px 20px;">
                                                    <h1 style="margin: 0; font-family: 'Montserrat', sans-serif; font-size: 30px; line-height: 36px; color: #ffffff; font-weight: bold;">Hello,</h1>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td valign="top" style="text-align: center; padding: 10px 20px 15px 20px; font-family: sans-serif;  font-size: 20px; line-height: 25px; color: #ffffff;">
                                                    <p style="margin: 0;">I couldn't update below Alum for syncing Raiser's Edge and AlmaBase.</p>
                                                </td>
                                            </tr>
                                            </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td height="20" style="font-size:20px; line-height:20px;">&nbsp;</td>
                                        </tr>
                                    </table>
                                    <!--[if mso]>
                                    </td>
                                    </tr>
                                    </table>
                                    <![endif]-->
                                </div>
                                <!--[if gte mso 9]>
                                </v:textbox>
                                </v:rect>
                                <![endif]-->
                            </td>
                        </tr>
                        <!-- HERO : END -->
                        <!-- INTRO : BEGIN -->
                        <tr>
                            <td bgcolor="#ffffff">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="padding: 40px 40px 20px 40px; text-align: left;">
                                            <h1 style="margin: 0; font-family: arial, cochin, sans-serif; font-size: 20px; line-height: 26px; color: #333333; font-weight: bold;">Below are the Alum details,</h1>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="left" style="padding: 0px 40px 20px 40px;">
                                    <table cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td width="30%" align="left" bgcolor="#eeeeee" style="font-family: Open Sans, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 800; line-height: 24px; padding: 10px;">
                                                Name
                                            </td>
                                            <td width="70%" align="left" bgcolor="#eeeeee" style="font-family: Open Sans, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 800; line-height: 24px; padding: 10px;">
                                                {{name}}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td width="30%" align="left" style="font-family: Open Sans, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 400; line-height: 24px; padding: 15px 10px 5px 10px;">
                                                Email Addresses
                                            </td>
                                            <td width="70%" align="left" style="font-family: Open Sans, Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 400; line-height: 24px; padding: 15px 10px 5px 10px;">
                                                <p>{{email_1}}</p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="left" style="padding-top: 20px;">
                                </td>
                                    </tr>
                                    <tr>
                                    </tr>
                                    <tr>
                                        <td style="padding: 0px 40px 0px 50px; font-family: sans-serif; font-size: 15px; line-height: 20px; color: #555555; text-align: left; font-weight:normal;">
                                            <p style="margin: 0;">Yours sincerely,</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="left" style="padding: 0px 40px 40px 40px;">
                                            <table width="200" align="left">
                                                <tr>
                                                    <td width="90">
                                                    <img src="https://i.ibb.co/J262D44/Bot.png" width="90" height="90" style="margin:0; padding:0; border:none; display:block;" border="0" alt="">
                                                    </td>
                                                    <td width="110">
                                                    <table width="" cellpadding="0" cellspacing="0" border="0">
                                                        <tr>
                                                        <td align="left" style="font-family: sans-serif; font-size:15px; line-height:20px; color:#222222; font-weight:bold;" class="body-text">
                                                            <p style="font-family: 'Montserrat', sans-serif; font-size:15px; line-height:20px; color:#222222; font-weight:bold; padding:0; margin:0;" class="body-text">A Bot,</p>
                                                        </td>
                                                        </tr>
                                                        <tr>
                                                        <td align="left" style="font-family: sans-serif; font-size:15px; line-height:20px; color:#666666;" class="body-text">
                                                            <p style="font-family: sans-serif; font-size:15px; line-height:20px; color:#666666; padding:0; margin:0;" class="body-text">made by Kamal.</p>
                                                        </td>
                                                        </tr>
                                                    </table>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- INTRO : END -->
                        <!-- CTA : BEGIN -->
                        <tr>
                            <td bgcolor="#26a4d3">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="padding: 40px 40px 5px 40px; text-align: center;">
                                            <h1 style="margin: 0; font-family: 'Montserrat', sans-serif; font-size: 20px; line-height: 24px; color: #ffffff; font-weight: bold;">YOU CAN CHECK THIS ALUMNI</h1>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 0px 40px 20px 40px; font-family: sans-serif; font-size: 17px; line-height: 23px; color: #aad4ea; text-align: center; font-weight:normal;">
                                            <p style="margin: 0;">in Raiser's Edge</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td valign="middle" align="center" style="text-align: center; padding: 0px 20px 40px 20px;">
                                            <!-- Button : BEGIN -->
                                            <table role="presentation" align="center" cellspacing="0" cellpadding="0" border="0" class="center-on-narrow">
                                                <tr>
                                                    <td style="border-radius: 50px; background: #ffffff; text-align: center;" class="button-td">
                                                        <a href="https://host.nxt.blackbaud.com/constituent/records/{{re_system_id}}?envid=p-dzY8gGigKUidokeljxaQiA&svcid=renxt" style="background: #ffffff; border: 15px solid #ffffff; font-family: 'Montserrat', sans-serif; font-size: 14px; line-height: 1.1; text-align: center; text-decoration: none; display: block; border-radius: 50px; font-weight: bold;" class="button-a">
                                                            <span style="color:#26a4d3;" class="button-link">&nbsp;&nbsp;&nbsp;&nbsp;CHECK NOW&nbsp;&nbsp;&nbsp;&nbsp;</span>
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>
                                            <!-- Button : END -->
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- CTA : END -->
                        <!-- SOCIAL : BEGIN -->
                        <tr>
                            <td bgcolor="#292828">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="padding: 30px 30px; text-align: center;">
                                            <table align="center" style="text-align: center;">
                                                <tr>
                                                    <td>
                                                        <h1 style="margin: 0; font-family: 'Montserrat', sans-serif; font-size: 20px; line-height: 24px; color: #ffffff; font-weight: bold;">Have a nice day! 😊</h1>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- SOCIAL : END -->
                        <!-- FOOTER : BEGIN -->
                        <tr>
                            <td bgcolor="#ffffff">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="padding: 40px 40px 0px 40px; font-family: sans-serif; font-size: 14px; line-height: 18px; color: #666666; text-align: center; font-weight:normal;">
                                            <p style="margin: 0;"><b>Indian Institute of Technology Bombay</b></p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 0px 40px 30px 40px; font-family: sans-serif; font-size: 12px; line-height: 18px; color: #666666; text-align: center; font-weight:normal;">
                                            <p style="margin: 0;">Powai, Mumbai, Maharashtra, India 400076</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- FOOTER : END -->
                    </table>
                    <!-- Email Body : END -->
                    <!--[if mso]>
                    </td>
                    </tr>
                    </table>
                    <![endif]-->
                </div>
            </center>
        </body>
        </html>
        """

        # Create a text/html message from a rendered template
        emailbody = MIMEText(
            Environment().from_string(TEMPLATE).render(
                name=name,
                email_1=address['address'],
                re_system_id=re_system_id
            ), "html"
        )

        # Add HTML parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(emailbody)
        emailcontent = message.as_string()
        
        # Create secure connection with server and send email
        context = ssl._create_unverified_context()
        with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
            server.login(MAIL_USERN, MAIL_PASSWORD)
            server.sendmail(
                MAIL_USERN, SEND_TO, emailcontent
            )

        # Save copy of the sent email to sent items folder
        with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
            imap.login(MAIL_USERN, MAIL_PASSWORD)
            imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
            imap.logout()
        
    exit()

def add_tags(attr_type, atrr_comment):
    
    print("Adding update tags for new updates in RE")
    
    global params, url
    
    url = 'https://api.sky.blackbaud.com/constituent/v1/constituents/customfields'
    
    if attr_type == 'email':
        value = 'AlmaBase - Automatically | Email address'
        
    elif attr_type == 'mobile':
        value = 'AlmaBase - Automatically | Phone Number'
        
    elif attr_type == 'employment':
        value = 'AlmaBase - Automatically | Employment - Org. Name'
        
    elif attr_type == 'position':
        value = 'AlmaBase - Automatically | Employment - Position'
        
    elif attr_type == 'location':
        value = 'AlmaBase - Automatically | Location'
        
    elif attr_type == 'education':
        value = 'AlmaBase - Automatically | Education'
        
    elif attr_type == 'bio':
        value = 'AlmaBase - Automatically | Bio Details'
        
    elif attr_type == 'online':
        value = 'AlmaBase - Automatically | Online Presence'
    
    comment = 'Update: ' + str(atrr_comment)
    
    params = {
        'category': 'Synced from',
        'parent_id': re_system_id,
        'value': value,
        'comment': comment,
        'date': datetime.now().replace(microsecond=0).isoformat()
    }
    
    # Blackbaud API POST request
    post_request_re()
    
    check_for_errors()

def update_email_in_re():
    print("Updating email in RE")
    time.sleep(5)
    global params
    params = {
        'address': email_address,
        'constituent_id': re_system_id,
        'type': new_email_type
    }
    
    global url
    url = "https://api.sky.blackbaud.com/constituent/v1/emailaddresses"
    
    # Blackbaud API POST request
    post_request_re()
    
    check_for_errors()
    
    # Adding Update Tags
    add_tags('email', email_address)

def del_blank_values_in_json(d):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    This alters the input so you may wish to ``copy`` the dict first.
    """
    # For Python 3, write `list(d.items())`; `d.items()` won’t work
    # For Python 2, write `d.items()`; `d.iteritems()` won’t work
    for key, value in list(d.items()):
        if value == "" or value == {} or value == [] or value == [""]:
            del d[key]
        elif isinstance(value, dict):
            del_blank_values_in_json(value)
    return d  # For convenience

def print_json(d):
    print(json.dumps(d, indent=4))

def get_address(address):
    print("Getting city, state and country from an Address")
    time.sleep(5)
    # initialize Nominatim API
    geolocator = Nominatim(user_agent="geoapiExercises")

    # adding 1 second padding between calls
    global geocode
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds = 1, return_value_on_exception = None)
    
    location = geolocator.geocode(address, addressdetails=True, language='en')

    if location is None:
        i = 0
    else:
        i = 1

    while i == 0:
        address_split = address[address.index(' ')+1:]
        address = address_split
        location = geolocator.geocode(address_split, addressdetails=True)
        
        if location is None:
            address = address_split
            try:
                if address == "":
                    break
            except:
                break
            i = 0
            
        if location is not None:
            break

    address = location.raw['address']
    
    global city
    try:
        city = address.get('city', '')
        if city == "":
            try:
                city = address.get('state_district', '')
                if city == "":
                    try:
                        city = address.get('county', '')
                    except:
                        city = ""
            except:
                try:
                    city = address.get('county', '')
                except:
                    city = ""
    except:
        try:
            city = address.get('state_district', '')
            if city == "":
                try:
                    city = address.get('county', '')
                except:
                    city = ""
        except:
            try:
                city = address.get('county', '')
            except:
                city = ""
    
    global state
    state = address.get('state', '')
    
    global country
    country = address.get('country', '')
    
    global zip
    zip = address.get('postcode', '')

try:
    # Query the next data to uploaded in RE
    print("Querying the next data to uploaded in RE")
    
    # Putting the subject in advance if error pops up
    # global subject
    subject = "No Alums available for sync. Sync has been completed"
    
    try:
        # Ensuring that Alum exists in Table
        extract_sql = """
            SELECT re_system_id FROM all_alums_in_re FETCH FIRST 1 ROW ONLY;
            """
        cur.execute(extract_sql)
        result = cur.fetchone()
        
        # Ensure no comma or brackets in output
        re_system_id = result[0]
        
        if re_system_id is None or re_system_id == '':
            print("Alums not downloaded in the table")
            subject = "No Alums available for sync. Alums not downloaded in the table"
            
            print(subject)

            # Commit changes
            conn.commit()
            
            notify_sync_finished()
            
        
        extract_sql = """
            SELECT re_system_id FROM all_alums_in_re WHERE re_system_id NOT IN (SELECT re_system_id FROM already_synced) 
            ORDER BY random()
            LIMIT 1;
            """
        cur.execute(extract_sql)
        result = cur.fetchone()

        # Ensure no comma or brackets in output
        re_system_id = result[0]
        print("Working on Alumni with RE ID: " + str(re_system_id))
    
    except:
        print(subject)
        
        # Delete rows in table
        cur.execute("truncate already_synced;")

        # Commit changes
        conn.commit()
        
        notify_sync_finished()

    # Get email list from RE
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/emailaddresses?include_inactive=true" % re_system_id

    params = {
            #'search_text':search_text
        }

    # Blackbaud API GET request
    get_request_re()

    count = 0
    while count != 1:
        # Search in AlmaBase
        print("Locating the Alum in Almabase")
        for address in re_api_response['value']:
            # try:
            email = (address['address'])
            url = "https://api.almabaseapp.com/api/v1/profiles?search=%s&page=1&listed=true" % email
            get_request_almabase()
            count = ab_api_response["count"]
            if count == 1:
                break
            
        if count != 1:
            subject = "Unable to find Alums in AlmaBase for sync"
            constituent_not_found_email()
                    
            # except:
            #     # Can't find Alum in AlmaBase
            #     status = ab_api_response["status"]
            #     if status == 404:
            #         subject = "Unable to find Alums in AlmaBase because of Network Failure"
            #     else:
            #         subject = "Unable to find Alums in AlmaBase for sync"
            #     constituent_not_found_email()
    else:
        ab_system_id = ab_api_response["results"][0]["id"]

    # Retrieve the AlmaBase Profile
    print("Got the Almabase ID: " + str(ab_system_id))
    url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id

    get_request_almabase()
    
    print("Fetching the Almabase profile")
    ab_profile = ab_api_response

    # Get email list from AlmaBase
    print("Getting email list from AlmaBase")
    ab_email_list = []
    for address in ab_profile['email_addresses']:
        try:
            emails = (address['address']).lower()
            
            if '@' in emails:
                ab_email_list.append(emails)
        except:
            pass

    # Get list of available custom fields starting with email_id_
    print("Getting list of available custom fields starting with email_id_")
    regex = re.compile('email_id_*')
    email_id_list_ab = [string for string in ab_profile['custom_fields'] if re.match(regex, string)]
    email_id_list_og = ["email_id_1", "email_id_2", "email_id_3", "email_id_4"]
    
    email_id_list_combo = email_id_list_ab + email_id_list_og
    
    email_id_list = []
    [email_id_list.append(x) for x in email_id_list_combo if x not in email_id_list]
    
    print_json(email_id_list)

    blank_email_ids = []
    for each_id in email_id_list:
        try:
            emails = (ab_profile['custom_fields'][each_id]['values'][0]['value']['content'])
            if '@' in emails:
                ab_email_list.append(emails)
        except:
            # Email IDs that don't have any email addresses in AlmaBase
            blank_email_ids.append(each_id)
            pass
    print("Email list in Almabase: " + str(ab_email_list))
    
    print("Getting email list from RE")
    re_email_list = []
    for address in re_api_response['value']:
        try:
            emails = (address['address']).lower()
            if '@' in emails:
                re_email_list.append(emails)
        except:
            pass
    print("Email list in RE: " + str(re_email_list))
        
    # Finding missing email addresses to be added in RE
    print("Finding missing email addresses to be added in RE")
    set1 = set([i for i in ab_email_list if i])
    set2 = set(re_email_list)

    missing_in_re = list(sorted(set1 - set2))
    print("Missing email addresses in RE: " + str(missing_in_re))

    # Will update missing email IDs to RE
    if missing_in_re != []:
        print("Updating the missing email IDs to RE")
        email_type_list = []
        for emails in missing_in_re:
            try:
                email_address = emails
                # Figure the email type
                types = address['type']
                email_num = re.sub("[^0-9]", "", types)
                # Checking if email_num is blank (when there's no Email 1, 2, etc.)
                if email_num == "":
                    email_num = 0
                email_type_list.append(email_num)
                existing_max_count = int(max(email_type_list))
                new_max_count = existing_max_count + 1
                try:
                    incremental_max_count
                except:
                    incremental_max_count = new_max_count
                else:
                    incremental_max_count = incremental_max_count + 1            
                # global new_email_type
                new_email_type = "Email " + str(incremental_max_count)
                update_email_in_re()
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO re_emails_added (re_system_id, email, date)
                                VALUES (%s, %s, now())
                                """
                cur.execute(insert_updates, [re_system_id, email_address])
                conn.commit()
                print("Updated all the missing email IDs to RE")
            except:
                send_error_emails()

    # Finding missing email addresses to be added in AlmaBase
    print("Finding missing email addresses to be added in AlmaBase")
    set1 = set([i for i in re_email_list if i])
    set2 = set(ab_email_list)

    missing_in_ab = list(sorted(set1 - set2))
    print("Missing email addresses in Almabase: " + str(missing_in_ab))
    print("Available email blank values in Almabase: " + str(blank_email_ids))
    
    print_json(ab_email_list)
    
    # Upload missing email addresses in AlmaBase
    if missing_in_ab != []:
        print("Updating the missing email IDs to Almabase")
        
        # ab_email_addresses = []
        
        # for each_record in ab_email_list:
        #     missing_in_ab.append(each_record)
            
        print(missing_in_ab)
        
        # for each_record in zip(missing_in_ab, blank_email_ids):
            
        #     each_email, each_id = each_record
        
        for each_record in missing_in_ab:
            
            # format = {
            #             'address': each_record,
            #             'is_engaged': 'false',
            #             'is_primary': 'false',
            #             'source': 'Raisers Edge',
            #             'is_login_email': 'true'
            #         }
                
            # ab_email_addresses.append(format)
            
            try:
                # each_email, each_id = each_record
                # params = {
                #     'custom_fields': {
                #         each_id: {
                #             'type': 'email',
                #             'label': each_id,      
                #             'values': [
                #                 {
                #                     'value': {
                #                         'content': each_email
                #                         },
                #                     'display_order': int(each_id[-2:].replace("_", ""))
                #                     }
                #                 ]
                #             }
                #         }
                #     }
                
                # params = {
                #     'email_addresses': ab_email_addresses
                # }
                
                params = {
                            'address': each_record,
                            'is_engaged': 'false',
                            'is_primary': 'false',
                            'source': 'Raisers Edge',
                            'is_login_email': 'true'
                        }
                
                print_json(params)
                
                # url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
                url = f"https://api.almabaseapp.com/api/v1/profiles/{ab_system_id}/email_addresses"
                    
                # patch_request_ab()
                post_request_ab()
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO ab_emails_added (ab_system_id, email, date)
                                VALUES (%s, %s, now())
                                """
                cur.execute(insert_updates, [ab_system_id, each_record])
                conn.commit()
                print("Updated all the missing email IDs to Almabase")
            except:
                send_error_emails()
        
    # Get list of of phone numbers in RE
    print("Get list of of phone numbers in RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/phones?include_inactive=true" % re_system_id
    params = {}
    get_request_re()

    re_phone_list = []
    for each_phone in re_api_response['value']:
        try:
            phones = re.sub("[^0-9]", "",(each_phone['number']))
            re_phone_list.append(phones)
        except:
            pass
    print("List of phone numbers in RE: " + str(re_phone_list))
        
    # Get list of phone numbers in AlmaBase
    print("Get list of phone numbers in AlmaBase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s/phone_numbers" % ab_system_id
    get_request_almabase()

    ab_phone_list = []
    for each_phone in ab_api_response['results']:
        try:
            phones = re.sub("[^0-9]", "",(each_phone['number']))
            ab_phone_list.append(phones)
        except:
            pass

    # Get list of available custom fields starting with phone, fax, mobile, pager
    print("Getting list of available custom fields starting with phone, fax, mobile, pager")
    regex = re.compile('\w+phone|\w+fax|\w+mobile|\w+pager')
    phone_id_list = [string for string in ab_profile['custom_fields'] if re.match(regex, string)]

    blank_phone_ids = []
    for each_id in phone_id_list:
        try:
            phones = re.sub("[^0-9]", "",(ab_profile['custom_fields'][each_id]['values'][0]['value']['content']))
            if len(phones) > 5:
                ab_phone_list.append(phones)
        except:
            # Email IDs that don't have any email addresses in AlmaBase
            blank_phone_ids.append(each_id)
            pass
    print("List of phone numbers in Almabase: " + str(ab_phone_list))

    # Finding missing phone numbers to be added in RE
    print("Finding missing phone numbers to be added in RE")
    missing_in_re = []
    for each_phone in ab_phone_list:
        try:
            likely_phone, score = process.extractOne(each_phone, re_phone_list)
            if score < 80:
                if len(each_phone) > 5:
                    missing_in_re.append(each_phone)
        except:
            if len(each_phone) > 5:
                missing_in_re.append(each_phone)

    # Making sure that there are no duplicates in the missing list
    print("Removing duplicates in the missing list")
    if missing_in_re != []:
        missing = list(process.dedupe(missing_in_re, threshold=80))
        missing_in_re = missing
        print("Missing phone numbers in RE: " + str(missing_in_re))

    # Upload missing numbers in RE
    if missing_in_re != []:
        print("Uploading missing numbers in RE")
        for each_phone in missing_in_re:
            
            url = "https://api.sky.blackbaud.com/constituent/v1/phones"
        
            params = {
                'constituent_id': re_system_id,
                'number': each_phone,
                'type': 'Mobile'
            }
            
            post_request_re()
            
            # Adding Update Tags
            add_tags('mobile', each_phone)
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_phone_added (re_system_id, phone, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [re_system_id, each_phone])
            conn.commit()
            
        print("Uploaded all missing numbers in RE")
            
    # Finding missing phone numbers to be added in AlmaBase
    print("Finding missing phone numbers to be added in AlmaBase")
    missing_in_ab = []
    for each_phone in re_phone_list:
        try:
            likely_phone, score = process.extractOne(each_phone, ab_phone_list)
            if score < 80:
                missing_in_ab.append(each_phone)
        except:
            missing_in_ab.append(each_phone)

    # Making sure that there are no duplicates in the missing list
    print("Making sure that there are no duplicates in the missing list")
    if missing_in_ab != []:
        missing = list(process.dedupe(missing_in_ab, threshold=80))
        missing_in_ab = missing
        print("Missing phone numbers in Almabase: " + str(missing_in_ab))

    # Upload missing numbers in AlmaBase
    if missing_in_ab != []:
        print("Uploading missing numbers in AlmaBase")
        for each_record in zip(missing_in_ab, blank_phone_ids):
            try:
                each_phone, each_id = each_record
                params = {
                                'custom_fields': {
                                    each_id: {
                                        'values': [
                                            {
                                                'value': {
                                                    'content': each_phone
                                                },
                                                'display_order': 0
                                            }
                                        ]
                                    }
                                }
                            }
                
                url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
                            
                patch_request_ab()
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO ab_phone_added (ab_system_id, phone, date)
                                VALUES (%s, %s, now())
                                """
                cur.execute(insert_updates, [ab_system_id, each_phone])
                conn.commit()
                print("Uploaded missing numbers in AlmaBase")
            except:
                send_error_emails()
                
    # Get Relation list from RE
    print("Getting Employment list from RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/relationships" % re_system_id
    params = {}
    get_request_re()

    re_api_response_org = re_api_response
    re_org_name_list = []

    for each_org in re_api_response['value']:
        try:
            if each_org['type'] == 'Employer' or each_org['type'] == 'Former Employer' or each_org['type'] == 'University':
                # Retrieve the org name
                re_org_name_list.append(each_org['name'])
        except:
            pass

    # Get Employment list from AlmaBase
    print("Getting Employment list from AlmaBase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s/employments" % ab_system_id
    get_request_almabase()

    ab_api_response_org = ab_api_response
    ab_org_name_list = []

    for each_org in ab_api_response['results']:
        try:
            # Retrieve the org name
            if each_org['employer']['name'] != "add-company" and each_org['employer']['name'] != "Unknown" and each_org['employer']['name'] != "x":
                ab_org_name_list.append(each_org['employer']['name'])
        except:
            pass

    # Finding missing employments to be added in RE
    print("Finding missing employments to be added in RE")
    missing_in_re = []
    for each_org in ab_org_name_list:
        try:
            likely_phone, score = process.extractOne(each_org, re_org_name_list)
            if score < 90:
                missing_in_re.append(each_org)
        except:
            missing_in_re.append(each_org)

    # Making sure that there are no duplicates in the missing list
    print("Making sure that there are no duplicates in the missing list")
    if missing_in_re != []:
        missing = list(process.dedupe(missing_in_re, threshold=80))
        missing_in_re = missing
    print("Missing employments in RE: " + str(missing_in_re))

    # Upload missing employments in RE
    if missing_in_re != []:
        print("Uploading missing employments in RE")
        for each_org in missing_in_re:
            if each_org != "add-company" and each_org != "Unknown" and each_org != "x":
                try:
                    for each_ab_org in ab_api_response_org['results']:
                        if each_org == each_ab_org['employer']['name']:
                            
                            try:
                                position = each_ab_org['designation']['name']
                                if position is None or position == "null" or position == "Null":
                                    position = ""
                            except:
                                position = ""
                                
                            try:
                                start_month = each_ab_org['start_month']
                                if start_month is None or start_month == "null" or start_month == "Null":
                                    start_month = ""
                            except:
                                start_month = ""
                            
                            try:
                                start_year = each_ab_org['start_year']
                                if start_year is None or start_year == "null" or start_year == "Null":
                                    start_year = ""
                            except:
                                start_year = ""
                            
                            try:
                                end_month = each_ab_org['end_month']
                                if end_month is None or end_month == "null" or end_month == "Null":
                                    end_month = ""
                            except:
                                end_month = ""
                            
                            try:
                                end_year = each_ab_org['end_year']
                                if end_year is None or end_year == "null" or end_year == "Null":
                                    end_year = ""
                            except:
                                end_year = ""
                                
                            break
                except:
                    pass
                
                # Check if organisation is a University
                print("Checking if the missing employments is a University")
                school_matches = ["school", "college", "university", "institute", "iit", "iim"]
                if any(x in each_org.lower() for x in school_matches):
                    relationship = "University"
                else:
                    relationship = "Employer"
                
                params_re = {
                    'constituent_id': re_system_id,
                    'relation': {
                        'name': each_org[:60],
                        'type': 'Organization'},
                    'position': position[:50],
                    'start': {
                        'm': start_month,
                        'y': start_year
                    },
                    'end': {
                        'm': end_month,
                        'y': end_year
                    },
                    'type': relationship,
                    'reciprocal_type': 'Employee'
                }
                
                # Delete blank values from JSON
                for i in range(10):
                    params = del_blank_values_in_json(params_re.copy())
                
                url = "https://api.sky.blackbaud.com/constituent/v1/relationships"
                
                post_request_re()
                
                check_for_errors()
                
                # Adding Update Tags
                add_tags('employment', each_org)
                
                print("Added missing employment")
        
    # Update missing details in RE
    print("Checking missing details from any existing employment...")
    for each_org in re_api_response_org['value']:
        if each_org != "add-company" and each_org != "Unknown" and each_org != "x":
            # Get values present in RE
            re_org_name = each_org['name']
            
            if 'position' in each_org:
                re_org_position = each_org['position']
            else:
                re_org_position = ""
                
            try:
                re_org_start_month = each_org['start']['m']
            except:
                re_org_start_month = ""
                
            try:
                re_org_start_year = each_org['start']['y']
            except:
                re_org_start_year = ""
            
            try:
                re_org_end_month = each_org['end']['m']
            except:
                re_org_end_month = ""
                
            try:
                re_org_end_year = each_org['end']['y']
            except:
                re_org_end_year = ""
            
            relationship_id = each_org['id']
            
            # Get values present in AlmaBase for above same organisation
            print("... by comparing the same organisation present in Almabase")
            for each_ab_org in ab_api_response_org['results']:
                if fuzz.token_set_ratio(re_org_name.lower(),each_ab_org['employer']['name'].lower()) >= 90:
                    
                    try:
                        if each_ab_org['designation']['name'] is not None:
                            ab_org_position = each_ab_org['designation']['name']
                        else:
                            ab_org_position = ""
                    except:
                        ab_org_position = ""
                    
                    try:
                        if each_ab_org['start_month'] is not None:
                            ab_org_start_month = each_ab_org['start_month']
                        else:
                            ab_org_start_month = ""
                    except:
                        ab_org_start_month = ""
                    
                    try:
                        if each_ab_org['start_year'] is not None:
                            ab_org_start_year = each_ab_org['start_year']
                        else:
                            ab_org_start_year = ""
                    except:
                        ab_org_start_year = ""
                    
                    try:
                        if each_ab_org['end_month'] is not None:
                            ab_org_end_month = each_ab_org['end_month']
                        else:
                            ab_org_end_month = ""
                    except:
                        ab_org_end_month = ""
                    
                    try:
                        if each_ab_org['end_year'] is not None:
                            ab_org_end_year = each_ab_org['end_year']
                        else:
                            ab_org_end_year = ""
                    except:
                        pass
                    
                    if ab_org_position == "" and ab_org_start_month == "" and ab_org_start_year == "" and ab_org_end_month == "" and ab_org_end_year == "":
                        break
                    else:
                        url = "https://api.sky.blackbaud.com/constituent/v1/relationships/%s" % relationship_id
                        
                        # Check if position needs an update
                        print("Checking if position needs an update")
                        if re_org_position != "" or ab_org_position == "":
                            ab_org_position = ""
                            
                        # Check if joining year needs an update
                        print("Checking if joining year needs an update")
                        if re_org_start_year != "" or ab_org_start_year == "":
                            ab_org_start_month = ""
                            ab_org_start_year = ""
                            
                        # Check if leaving year needs an update
                        print("Checking if leaving year needs an update")
                        if re_org_end_year != "" or ab_org_end_year == "":
                            ab_org_end_month = ""
                            ab_org_end_year = ""
                        
                        params_re = {
                                'position': ab_org_position[:50],
                                'start': {
                                    'm': ab_org_start_month,
                                    'y': ab_org_start_year
                                },
                                'end': {
                                    'm': ab_org_end_month,
                                    'y': ab_org_end_year
                                }
                            }
                        
                        # Delete blank values from JSON
                        for i in range(10):
                            params = del_blank_values_in_json(params_re.copy())

                        if params != {}:
                            # Update in RE
                            patch_request_re()
                            
                            check_for_errors()
                            
                            # Adding Update Tags
                            add_tags('position', params)

                            print("Updated missing employment details in RE")
        
    # Finding missing employments to be added in AlmaBase
    print("Finding missing employments to be added in AlmaBase")
    missing_in_ab = []
    for each_org in re_org_name_list:
        try:
            likely_phone, score = process.extractOne(each_org, ab_org_name_list)
            if score < 90:
                if each_org != '' or each_org != "":
                    missing_in_ab.append(each_org)
        except:
            if each_org != '' or each_org != "":
                missing_in_ab.append(each_org)
        
    # Making sure that there are no duplicates in the missing list
    print("Making sure that there are no duplicates in the missing list")
    if missing_in_ab != []:
        missing = list(process.dedupe(missing_in_ab, threshold=80))
        missing_in_ab = missing
    print("Missing employments in Almabase: " + str(missing_in_ab))

    # Upload missing employments in Almabase
    if missing_in_ab != []:
        print("Uploading missing employments in Almabase")
        for each_org in missing_in_ab:
            for each_re_org in re_api_response_org['value']:
                if each_org == each_re_org['name']:
                    
                    try:
                        position = each_re_org['position']
                    except:
                        position = ""
                    
                    try:
                        start_month = each_re_org['start']['m']
                    except:
                        start_month = ""
                    
                    try:
                        start_year = each_re_org['start']['y']
                    except:
                        start_year = ""
                    
                    try:
                        end_month = each_re_org['end']['m']
                    except:
                        end_month = ""
                    
                    try:
                        end_year = each_re_org['end']['y']
                    except:
                        end_year = ""
                        
                    if position == "" and start_month == "" and start_year == "" and end_month == "" and end_year == "":
                        break
                    else:
                        # Create an employment in Almabase
                        print("Creating an employment in Almabase")
                        url = "https://api.almabaseapp.com/api/v1/profiles/%s/employments" % ab_system_id
                        
                        params_ab = {
                            'employer': {
                                'name': each_org
                            },
                            'designation': {
                                'name': position
                            },
                            'start_month': start_month,
                            'start_year': start_year,
                            'end_month': end_month,
                            'end_year': end_year
                        }
                        
                        # Delete blank values from JSON
                        for i in range(10):
                            params = del_blank_values_in_json(params_ab.copy())
                        
                        # Update in Almabase
                        post_request_ab()
                        print("Added missing employment in Almabase")
                    break

    # Update missing details in AlmaBase
    print("Updating missing details in AlmaBase")
    for each_org in ab_api_response_org['results']:
        # Get values present in AB
        ab_org_name = each_org['employer']['name']
        
        try:
            if each_org['designation']['name'] is not None:
                ab_org_position = each_org['designation']['name']
            else:
                ab_org_position = ""
        except:
            ab_org_position = ""
            
        try:
            if each_org['start_month'] is not None:
                ab_org_start_month = each_org['start_month']
            else:
                ab_org_start_month = ""
        except:
            ab_org_start_month = ""
            
        try:
            if each_org['start_year'] is not None:
                ab_org_start_year = each_org['start_year']
            else:
                ab_org_start_year = ""
        except:
            ab_org_start_year = ""
            
        try:
            if each_org['end_month'] is not None:
                ab_org_end_month = each_org['end_month']
            else:
                ab_org_end_month = ""
        except:
            ab_org_end_month = ""
            
        try:
            if each_org['end_year'] is not None:
                ab_org_end_year = each_org['end_year']
            else:
                ab_org_end_year = ""
        except:
            ab_org_end_year = ""
        
        ab_org_relationship_id = each_org['id']

        # Get values present in RE for above same organisation
        print("Getting values present in RE for the same organisation")
        for each_re_org in re_api_response_org['value']:
            if fuzz.token_set_ratio(ab_org_name.lower(),each_re_org['name'].lower()) >= 90:
                
                try:
                    re_org_position = each_re_org['position']
                except:
                    re_org_position = ""
                
                try:
                    re_org_start_month = each_re_org['start']['m']
                except:
                    re_org_start_month = ""
                
                try:
                    re_org_start_year = each_re_org['start']['y']
                except:
                    re_org_start_year = ""
                
                try:
                    re_org_end_month = each_re_org['end']['m']
                except:
                    re_org_end_month = ""
                
                try:
                    re_org_end_year = each_re_org['end']['y']
                except:
                    re_org_end_year = ""
                
                if re_org_position == "" and re_org_start_month == "" and re_org_start_year == "" and re_org_end_month == "" and re_org_end_year == "":
                    break
                else:
                    url = "https://api.almabaseapp.com/api/v1/profiles/%s/employments/%s" % (ab_system_id, ab_org_relationship_id)
                    
                    # Check if position needs an update
                    print("Checking if position needs an update")
                    if re_org_position == "" or ab_org_position != "":
                        re_org_position = ""
                        
                    # Check if joining year needs an update
                    print("Checking if joining year needs an update")
                    if re_org_start_year == "" or ab_org_start_year != "":
                        re_org_start_month = ""
                        re_org_start_year = ""
                        
                    # Check if leaving year needs an update
                    print("Checking if leaving year needs an update")
                    if re_org_end_year == "" or ab_org_end_year != "":
                        re_org_end_month = ""
                        re_org_end_year = ""

                    params_ab = {
                            'designation': {
                                'name': re_org_position
                            },
                            'start_month': re_org_start_month,
                            'start_year': re_org_start_year,
                            'end_month': re_org_end_month,
                            'end_year': re_org_end_year
                        }
                    
                    # Delete blank values from JSON
                    for i in range(10):
                        params = del_blank_values_in_json(params_ab.copy())
                        
                    if params != {}:           
                        patch_request_ab()
                        print("Updated employment details in Almabase")

    # for i in range(10):
    #     # Retrieve addresses from RE
    #     print("Retrieving addresses from RE")
    #     url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/addresses?include_inactive=true" % re_system_id
    #     params = {}
    #     get_request_re()

    #     re_api_response_address = re_api_response

    #     # Retrieve addresses from Almabase - 1
    #     print("Retrieving addresses from Almabase")
    #     url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=addresses" % ab_system_id

    #     get_request_almabase()
    #     ab_api_response_address = ab_api_response

    #     # Retrieve addresses from Almabase - 2
    #     url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=custom_fields" % ab_system_id

    #     get_request_almabase()
    #     ab_api_response_address_custom_fields = ab_api_response

    #     # Retrieve details from Permanent address in AlmaBase
    #     print("Retrieving details from Permanent address in AlmaBase")
    #     try:
    #         ab_permanent_address_line_1 = ab_api_response_address_custom_fields['custom_fields']['permanent_address']['values'][0]['value']['content']
    #     except:
    #         ab_permanent_address_line_1 = ""

    #     try:
    #         ab_permanent_address_line_2 = ab_api_response_address_custom_fields['custom_fields']['permanent_address_line_2']['values'][0]['value']['content']
    #     except:
    #         ab_permanent_address_line_2 = ""

    #     try:
    #         ab_permanent_address_city = ab_api_response_address_custom_fields['custom_fields']['permanent_city']['values'][0]['value']['content']
    #     except:
    #         ab_permanent_address_city = ""

    #     try:
    #         ab_permanent_address_state = ab_api_response_address_custom_fields['custom_fields']['permanent_state']['values'][0]['value']['content']
    #     except:
    #         ab_permanent_address_state = ""

    #     try:
    #         ab_permanent_address_country = ab_api_response_address_custom_fields['custom_fields']['permanent_country']['values'][0]['value']['content']
    #     except:
    #         ab_permanent_address_country = ""

    #     try:
    #         ab_permanent_address_zip = ab_api_response_address_custom_fields['custom_fields']['permanent_postal_code']['values'][0]['value']['content']
    #     except:
    #         ab_permanent_address_zip = ""
            
    #     ab_permanent_address = ab_permanent_address_line_1 + ab_permanent_address_line_2 + ab_permanent_address_city + ab_permanent_address_state + ab_permanent_address_country + ab_permanent_address_zip

    #     # Retrive details from Work address in AlmaBase
    #     print("Retrieving details from Work address in AlmaBase")
    #     try:
    #         ab_work_address_line_1 = ab_api_response_address_custom_fields['custom_fields']['work_address_line_1']['values'][0]['value']['content']
    #     except:
    #         ab_work_address_line_1 = ""

    #     try:
    #         ab_work_address_line_2 = ab_api_response_address_custom_fields['custom_fields']['work_address_line_2']['values'][0]['value']['content']
    #     except:
    #         ab_work_address_line_2 = ""

    #     try:
    #         ab_work_address_city = ab_api_response_address_custom_fields['custom_fields']['work_city']['values'][0]['value']['content']
    #     except:
    #         ab_work_address_city = ""

    #     try:
    #         ab_work_address_state = ab_api_response_address_custom_fields['custom_fields']['work_state']['values'][0]['value']['content']
    #     except:
    #         ab_work_address_state = ""

    #     try:
    #         ab_work_address_country = ab_api_response_address_custom_fields['custom_fields']['work_country']['values'][0]['value']['content']
    #     except:
    #         ab_work_address_country = ""

    #     try:
    #         ab_work_address_zip = ab_api_response_address_custom_fields['custom_fields']['work_postal_code']['values'][0]['value']['content']
    #     except:
    #         ab_work_address_zip = ""
        
    #     ab_work_address = ab_work_address_line_1 + ab_work_address_line_2 + ab_work_address_city + ab_work_address_state + ab_work_address_country + ab_work_address_zip
            
    #     ab_api_response_address_custom_fields_json = {
    #         'addresses': [
    #             {
    #                 'line1': ab_permanent_address_line_1,
    #                 'line2': ab_permanent_address_line_2,
    #                 'zip_code': ab_permanent_address_zip,
    #                 'location': {
    #                     'city': ab_permanent_address_city,
    #                     'state': ab_permanent_address_state,
    #                     'country': ab_permanent_address_country
    #                     }
    #             },
    #             {
    #                 'line1': ab_work_address_line_1,
    #                 'line2': ab_work_address_line_2,
    #                 'zip_code': ab_work_address_zip,
    #                 'location': {
    #                     'city': ab_work_address_city,
    #                     'state': ab_work_address_state,
    #                     'country': ab_work_address_country
    #                     }
    #             }
    #         ]
    #     }

    #     # Merge JSON strings into one
    #     for each_address in ab_api_response_address_custom_fields_json['addresses']:
    #         if each_address != '' and each_address != "":
    #             ab_api_response_address['addresses'].append(each_address)

    #     # Compare the ones in RE with AB and find delta
    #     print("Compare the addresses in RE with AB and find delta")
    #     re_address_list = []
    #     for each_value in re_api_response_address['value']:
    #         re_address = each_value['formatted_address'].replace("\r\n",", ")
    #         if re_address != '' and re_address != "":
    #             re_address_list.append(re_address)

    #     # Finding missing addresses to be added in RE
    #     print("Finding missing addresses to be added in RE")
    #     missing_in_re = []
    #     for each_value in ab_api_response_address['addresses']:
    #         try:
    #             try:
    #                 line1 = each_value['line1']
    #                 if line1 is None:
    #                     line1 = ""
    #             except:
    #                 line1 = ""
                    
    #             try:
    #                 line2 = each_value['line2']
    #                 if line2 is None:
    #                     line2 = ""
    #             except:
    #                 line2 = ""
                
    #             try:
    #                 city = each_value['location']['city']
    #                 if city is None:
    #                     city = ""
    #             except:
    #                 city = ""
                
    #             try:
    #                 state = each_value['location']['state']
    #                 if state is None:
    #                     state = ""
    #             except:
    #                 try:
    #                     state = each_value['location']['county']
    #                     if state is None:
    #                         state = ""
    #                 except:
    #                     state = ""
                        
    #             try:
    #                 country = each_value['location']['country']
    #                 if country is None:
    #                     country = ""
    #             except:
    #                 country = ""
                    
    #             try:
    #                 zip_code = each_value['zip_code']
    #                 if zip_code is None:
    #                     zip_code = ""
    #             except:
    #                 zip_code = ""
                
    #             if  line1 != "" or line2 != "" or city != "" or state != "" or country != "" or zip_code != "":
    #                 ab_address = line1 + " " + line2 + " " + city + " " + state + " " + country + " " + zip_code
                    
    #                 try:
    #                     likely_address, score = process.extractOne(ab_address, re_address_list)
    #                     if score < 80:
    #                         if ab_address != '' or ab_address != "":
    #                             missing_in_re.append(ab_address)
    #                 except:
    #                     if ab_address != '' or ab_address != "":
    #                             missing_in_re.append(ab_address)
    #         except:
    #             pass

    #     # Making sure that there are no duplicates in the missing list
    #     if missing_in_re != []:
    #         missing = list(process.dedupe(missing_in_re, threshold=80))
    #         missing_in_re = missing
    #         print("Addresses missing in RE: " + str(missing_in_re))

    #     # Create missing address in RE
    #     if missing_in_re != []:
    #         print("Adding missing addresses in RE")
    #         for address in missing_in_re:
    #             try:
    #                 # Get city, state and country from Address
    #                 get_address(address)
                    
    #                 url = "https://api.sky.blackbaud.com/constituent/v1/addresses"
                    
    #                 params = {
    #                     'constituent_id': re_system_id,
    #                     'type': 'Business',
    #                     'address_lines': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, ""),
    #                     'city': city,
    #                     'county': state,
    #                     'country': country,
    #                     'postal_code': zip
    #                 }
                    
    #                 post_request_re()
                    
    #                 # Will update in PostgreSQL
    #                 insert_updates = """
    #                                 INSERT INTO re_address_added (re_system_id, address, date)
    #                                 VALUES (%s, %s, now())
    #                                 """
    #                 cur.execute(insert_updates, [re_system_id, address])
    #                 conn.commit()
    #                 print("Added missing addresses in RE")
    #             except:
    #                 pass

    #     # Compare the ones in AB with RE and find delta
    #     print("Comparing the addresses in AB with RE and finding delta")
    #     ab_address_list = []
        
    #     for each_value in ab_api_response_address['addresses']:
            
    #         try:
    #             line1 = each_value['line1']
    #             if line1 is None:
    #                 line1 = ""
    #         except:
    #             line1 = ""
                
    #         try:
    #             line2 = each_value['line2']
    #             if line2 is None:
    #                 line2 = ""
    #         except:
    #             line2 = ""
            
    #         try:
    #             city = each_value['location']['city']
    #             if city is None:
    #                 city = ""
    #         except:
    #             city = ""
            
    #         try:
    #             state = each_value['location']['state']
    #             if state is None:
    #                 state = ""
    #         except:
    #             try:
    #                 state = each_value['location']['county']
    #                 if state is None:
    #                     state = ""
    #             except:
    #                 state = ""
                    
    #         try:
    #             country = each_value['location']['country']
    #             if country is None:
    #                 country = ""
    #         except:
    #             country = ""
                
    #         try:
    #             zip_code = each_value['zip_code']
    #             if zip_code is None:
    #                 zip_code = ""
    #         except:
    #             zip_code = ""
                
    #         ab_address = (line1 + " " + line2 + " " + city + " " + state + " " + country + " " + zip_code).replace("  ", " ")
    #         ab_address_list.append(ab_address)

    #     # Finding missing addresses to be added in AlmaBase
    #     print("Finding missing addresses to be added in AlmaBase")
    #     missing_in_ab = []
    #     for each_value in re_api_response_address['value']:
    #         if each_value != '' or each_value != "":
    #             re_address = each_value['formatted_address'].replace("\r\n",", ")
            
    #         try:
    #             likely_address, score = process.extractOne(re_address, ab_address_list)
    #             if score < 80:
    #                 if re_address != '' or re_address != "":
    #                     missing_in_ab.append(re_address)
    #         except:
    #             if re_address != '' or re_address != "":
    #                 missing_in_ab.append(re_address)

    #     # Making sure that there are no duplicates in the missing list
    #     print("Making sure that there are no duplicates in the missing list")
    #     if missing_in_ab != []:
    #         missing = list(process.dedupe(missing_in_ab, threshold=80))
    #         missing_in_ab = missing
    #         print("Missing addresses in Almabase: " + str(missing_in_ab))

    #     # Create missing address in AB
    #     if missing_in_ab != []:
    #         print("Adding missing address in Almabase")
    #         i = ab_profile['addresses'][0]['location']['type']
    #         for address in missing_in_ab:
    #             try:
    #                 # Check where the new address can be added
    #                 print("Checking where the new address can be added in Almabase")
    #                 while i > 0:
    #                     for each_value in ab_api_response_address['addresses']:
    #                         try:
    #                             line1 = each_value['line1']
    #                             if line1 is None:
    #                                 line1 = " "
    #                         except:
    #                             line1 = " "
                                
    #                         try:
    #                             line2 = each_value['line2']
    #                             if line2 is None:
    #                                 line2 = " "
    #                         except:
    #                             line2 = " "
                            
    #                         try:
    #                             city = each_value['location']['city']
    #                             if city is None:
    #                                 city = ""
    #                         except:
    #                             city = ""
                            
    #                         try:
    #                             state = each_value['location']['state']
    #                             if state is None:
    #                                 state = ""
    #                         except:
    #                             try:
    #                                 state = each_value['location']['county']
    #                                 if state is None:
    #                                     state = ""
    #                             except:
    #                                 state = ""
                                    
    #                         try:
    #                             country = each_value['location']['country']
    #                             if country is None:
    #                                 country = ""
    #                         except:
    #                             country = ""
                                
    #                         try:
    #                             zip_code = each_value['zip_code']
    #                             if zip_code is None:
    #                                 zip_code = ""
    #                         except:
    #                             zip_code = ""
                            
    #                         if line1 != "" and line2 != "" and city != "" and state != "" and country != country and zip_code != "":
    #                             i += 1
                                
    #                             # Stop after 4 addresses
    #                             if i == 4:
    #                                 break
    #                     else:
    #                         break
                    
    #                 # if i == 1:
    #                 #     ab_address_number = i + 2
    #                 # else:
    #                 #     ab_address_number = i + 1
    #                 ab_address_number = i + 1
                    
    #                 # Get city, state and country from Address
    #                 get_address(address)
                    
    #                 # Patch Profile
    #                 url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
                    
    #                 # Will add as address
    #                 if ab_address_number == 2:
    #                     print("Will add the new location as Address")  
                        
    #                     params = {
    #                         'addresses': [
    #                             {
    #                                 'line1': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, ""),
    #                                 'zip_code': zip,
    #                                 'location': {
    #                                     'name': city + ", " + state + ", " + country,
    #                                     "type": ab_address_number
    #                                 },
    #                                 "type": ab_address_number
    #                             }
    #                         ]
    #                     }
                    
    #                 # Will add as custom field - permanent address   
    #                 elif ab_address_number == 3:
    #                     print("Will add the new location as custom field - permanent address")  
                        
    #                     params = {
    #                         'custom_fields': {
    #                             'permanent_address': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, "")
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'permanent_city': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': city
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'permanent_state': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': state
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'permanent_country': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': country
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'permanent_postal_code': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': zip
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             }
    #                         }
    #                     }
                    
    #                 # Will add as address
    #                 elif ab_address_number == 4:
    #                     print("Will add the new location as Address")
                        
    #                     print("Will add the new location as custom field - work address")  
    #                     params = {
    #                         'custom_fields': {
    #                             'work_address_line_1': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, "")
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'work_city': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': city
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'work_state': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': state
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'work_country': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': country
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             },
    #                             'work_postal_code': {
    #                                 'values': [
    #                                     {
    #                                         'value': {
    #                                             'content': zip
    #                                         },
    #                                         'display_order': 0
    #                                     }
    #                                 ]
    #                             }
    #                         }
    #                     }
                    
    #                 elif ab_address_number == 0:
    #                     params = {
    #                         'addresses': [
    #                             {
    #                                 'line1': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, ""),
    #                                 'zip_code': zip,
    #                                 'location': {
    #                                     'name': city + ", " + state + ", " + country,
    #                                     "type": ab_address_number
    #                                 },
    #                                 "type": ab_address_number
    #                             }
    #                         ]
    #                     }
                    
    #                 patch_request_ab()
    #                 i += 1
                    
    #                 # Will update in PostgreSQL
    #                 insert_updates = """
    #                                 INSERT INTO ab_address_added (ab_system_id, address, date)
    #                                 VALUES (%s, %s, now())
    #                                 """
    #                 cur.execute(insert_updates, [ab_system_id, address])
    #                 conn.commit()
    #                 print("Added the missing address in Almabase")
    #             except:
    #                 pass
    
    # Retrieve addresses from RE
    print("Retrieving addresses from RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/addresses?include_inactive=true" % re_system_id
    params = {}
    get_request_re()

    re_api_response_address = re_api_response

    # Retrieve addresses from Almabase - 1
    print("Retrieving addresses from Almabase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=addresses" % ab_system_id

    get_request_almabase()
    ab_api_response_address = ab_api_response

    # Retrieve addresses from Almabase - 2
    url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=custom_fields" % ab_system_id

    get_request_almabase()
    ab_api_response_address_custom_fields = ab_api_response

    # Retrieve details from Permanent address in AlmaBase
    print("Retrieving details from Permanent address in AlmaBase")
    try:
        ab_permanent_address_line_1 = ab_api_response_address_custom_fields['custom_fields']['permanent_address']['values'][0]['value']['content']
    except:
        ab_permanent_address_line_1 = ""

    try:
        ab_permanent_address_line_2 = ab_api_response_address_custom_fields['custom_fields']['permanent_address_line_2']['values'][0]['value']['content']
    except:
        ab_permanent_address_line_2 = ""

    try:
        ab_permanent_address_city = ab_api_response_address_custom_fields['custom_fields']['permanent_city']['values'][0]['value']['content']
    except:
        ab_permanent_address_city = ""

    try:
        ab_permanent_address_state = ab_api_response_address_custom_fields['custom_fields']['permanent_state']['values'][0]['value']['content']
    except:
        ab_permanent_address_state = ""

    try:
        ab_permanent_address_country = ab_api_response_address_custom_fields['custom_fields']['permanent_country']['values'][0]['value']['content']
    except:
        ab_permanent_address_country = ""

    try:
        ab_permanent_address_zip = ab_api_response_address_custom_fields['custom_fields']['permanent_postal_code']['values'][0]['value']['content']
    except:
        ab_permanent_address_zip = ""
        
    ab_permanent_address = (ab_permanent_address_line_1 + ab_permanent_address_line_2 + ab_permanent_address_city + ab_permanent_address_state + ab_permanent_address_country + ab_permanent_address_zip).replace(" ", "")

    # Retrive details from Work address in AlmaBase
    print("Retrieving details from Work address in AlmaBase")
    try:
        ab_work_address_line_1 = ab_api_response_address_custom_fields['custom_fields']['work_address_line_1']['values'][0]['value']['content']
    except:
        ab_work_address_line_1 = ""

    try:
        ab_work_address_line_2 = ab_api_response_address_custom_fields['custom_fields']['work_address_line_2']['values'][0]['value']['content']
    except:
        ab_work_address_line_2 = ""

    try:
        ab_work_address_city = ab_api_response_address_custom_fields['custom_fields']['work_city']['values'][0]['value']['content']
    except:
        ab_work_address_city = ""

    try:
        ab_work_address_state = ab_api_response_address_custom_fields['custom_fields']['work_state']['values'][0]['value']['content']
    except:
        ab_work_address_state = ""

    try:
        ab_work_address_country = ab_api_response_address_custom_fields['custom_fields']['work_country']['values'][0]['value']['content']
    except:
        ab_work_address_country = ""

    try:
        ab_work_address_zip = ab_api_response_address_custom_fields['custom_fields']['work_postal_code']['values'][0]['value']['content']
    except:
        ab_work_address_zip = ""
        
    ab_work_address = (ab_work_address_line_1 + ab_work_address_line_2 + ab_work_address_city + ab_work_address_state + ab_work_address_country + ab_work_address_zip).replace(" ", "")
        
    ab_api_response_address_custom_fields_json = {
        'addresses': [
            {
                'line1': ab_permanent_address_line_1,
                'line2': ab_permanent_address_line_2,
                'zip_code': ab_permanent_address_zip,
                'location': {
                    'city': ab_permanent_address_city,
                    'state': ab_permanent_address_state,
                    'country': ab_permanent_address_country
                    }
            },
            {
                'line1': ab_work_address_line_1,
                'line2': ab_work_address_line_2,
                'zip_code': ab_work_address_zip,
                'location': {
                    'city': ab_work_address_city,
                    'state': ab_work_address_state,
                    'country': ab_work_address_country
                    }
            }
        ]
    }

    # Merge JSON strings into one
    for each_address in ab_api_response_address_custom_fields_json['addresses']:
        if each_address != '' and each_address != "" and each_address != " ":
            ab_api_response_address['addresses'].append(each_address)

    # Compare the ones in RE with AB and find delta
    print("Compare the addresses in RE with AB and find delta")
    re_address_list = []
    for each_value in re_api_response_address['value']:
        re_address = each_value['formatted_address'].replace("\r\n",", ")
        if re_address != '' and re_address != "" and re_address != " ":
            re_address_list.append(re_address)

    # Finding missing addresses to be added in RE
    print("Finding missing addresses to be added in RE")
    missing_in_re = []
    for each_value in ab_api_response_address['addresses']:
        try:
            try:
                line1 = each_value['line1']
                if line1 is None or line1 == 'Other':
                    line1 = ""
            except:
                line1 = ""
                
            try:
                line2 = each_value['line2']
                if line2 is None or line2 == 'Other':
                    line2 = ""
            except:
                line2 = ""
            
            try:
                city = each_value['location']['city']
                if city is None or city == 'Other':
                    city = ""
            except:
                city = ""
            
            try:
                state = each_value['location']['state']
                if state is None or state == 'Other':
                    state = ""
            except:
                try:
                    state = each_value['location']['county']
                    if state is None or state == 'Other':
                        state = ""
                except:
                    state = ""
                    
            try:
                country = each_value['location']['country']
                if country is None or country == 'Other':
                    country = ""
            except:
                country = ""
                
            try:
                zip_code = each_value['zip_code']
                if zip_code is None or zip_code == 'Other':
                    zip_code = ""
            except:
                zip_code = ""
            
            if  line1 != "" or line2 != "" or city != "" or state != "" or country != "" or zip_code != "":
                ab_address = line1 + " " + line2 + " " + city + " " + state + " " + country + " " + zip_code
                
                try:
                    if ab_address != '' and ab_address != "" and ab_address != " ":
                        likely_address, score = process.extractOne(ab_address, re_address_list)
                        if score < 80:
                            missing_in_re.append(ab_address)
                except:
                    if ab_address != '' and ab_address != "" and ab_address != " ":
                            missing_in_re.append(ab_address)
        except:
            pass

    # Making sure that there are no duplicates in the missing list
    if missing_in_re != []:
        missing = list(process.dedupe(missing_in_re, threshold=80))
        missing_in_re = missing
        print("Addresses missing in RE: " + str(missing_in_re))

    # Create missing address in RE
    if missing_in_re != []:
        print("Adding missing addresses in RE")
        for address in missing_in_re:
            
            # Get city, state and country from Address
            get_address(address)
            
            url = "https://api.sky.blackbaud.com/constituent/v1/addresses"
            
            params = {
                'constituent_id': re_system_id,
                'type': 'Business',
                'address_lines': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, ""),
                'city': city,
                'county': state,
                'country': country,
                'postal_code': zip
            }
            
            post_request_re()
            
            check_for_errors()
            
            # Adding Update Tags
            add_tags('location', address)
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_address_added (re_system_id, address, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [re_system_id, address])
            conn.commit()
            print("Added missing addresses in RE")

    # Compare the ones in AB with RE and find delta
    print("Comparing the addresses in AB with RE and finding delta")
    ab_address_list = []

    for each_value in ab_api_response_address['addresses']:
        
        try:
            line1 = each_value['line1']
            if line1 is None or line1 == 'Other':
                line1 = ""
        except:
            line1 = ""
            
        try:
            line2 = each_value['line2']
            if line2 is None or line2 == 'Other':
                line2 = ""
        except:
            line2 = ""
        
        try:
            city = each_value['location']['city']
            if city is None or city == 'Other':
                city = ""
        except:
            city = ""
        
        try:
            state = each_value['location']['state']
            if state is None or state == 'None':
                state = ""
        except:
            try:
                state = each_value['location']['county']
                if state is None or state == 'None':
                    state = ""
            except:
                state = ""
                
        try:
            country = each_value['location']['country']
            if country is None or country == 'None':
                country = ""
        except:
            country = ""
            
        try:
            zip_code = each_value['zip_code']
            if zip_code is None or zip_code == 'None':
                zip_code = ""
        except:
            zip_code = ""
            
        ab_address = (line1 + " " + line2 + " " + city + " " + state + " " + country + " " + zip_code).replace("  ", " ").replace("  ", " ").replace("  ", " ")
        if ab_address != "" and ab_address != " " and ab_address != 'Other' and ab_address != 'India':
            ab_address_list.append(ab_address)

    # Finding missing addresses to be added in AlmaBase
    print("Finding missing addresses to be added in AlmaBase")
    missing_in_ab = []
    for each_value in re_api_response_address['value']:
        if each_value != '' and each_value != "" and each_value != " " and each_value != 'India':
            re_address = each_value['formatted_address'].replace("\r\n",", ")
        
        try:
            if re_address != "" and re_address != " " and re_address != 'India':
                likely_address, score = process.extractOne(re_address, ab_address_list)
                if score < 80:
                    missing_in_ab.append(re_address)
        except:
            if re_address != " " and re_address != "" and re_address != 'India':
                missing_in_ab.append(re_address)

    # Making sure that there are no duplicates in the missing list
    print("Making sure that there are no duplicates in the missing list")
    if missing_in_ab != []:
        missing = list(process.dedupe(missing_in_ab, threshold=80))
        # Removing blank strings
        missing_in_ab = [x.strip() for x in missing if x.strip()]
        print("Missing addresses in Almabase: " + str(missing_in_ab))
        
    # Identifying which Address slot is blank in Almabase
    print("Identifying which Address slot is blank in Almabase")
    almabase_slots = [1, 2, 3, 4]

    consumed_slot = []
    print_json(ab_api_response_address)
    
    try:
        for each_type in ab_api_response_address['addresses']:
            consumed_slot.append(each_type['type'])
    except:
        pass

    if ab_permanent_address != "":
        slot = 3
        consumed_slot.append(slot)

    if ab_work_address != "":
        slot = 4
        consumed_slot.append(slot)

    available_slots = set(almabase_slots) - set(consumed_slot)
    if available_slots == set() or available_slots == "" or available_slots == {}:
        available_slots = 0
    print("Available address slots in Almabase: " + str(available_slots))

    # Create missing address in AB
    if missing_in_ab != [] and available_slots != 0:
        # Patch Profile
        url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
        
        print("Adding missing address in Almabase")
        
        updated_address = []
        
        for address in missing_in_ab:
            # Check where the new address can be added
            print("Checking where the new address can be added in Almabase")
            for ab_address_number in available_slots:
                
                if missing_in_ab != {} or available_slots != {}:
            
                    # Get city, state and country from Address
                    get_address(address)
                    
                    existing_address = {'addresses': []}
                    
                    # Will add as address
                    if int(ab_address_number) == 1 or int(ab_address_number) == 2:
                        print("Will add the new location as Address")
                        
                        print(ab_address_number)
                        
                        if int(ab_address_number) == 2:
                            try:
                                for home_address in ab_api_response_address['addresses']:
                                    print("Getting existing home address")
                                    print(home_address['type'])
                                    if home_address['type'] == 1:
                                        existing_address = {
                                            'addresses': [
                                                {
                                                    'line1': home_address['line1'],
                                                'zip_code': home_address['zip_code'],
                                                'location': {
                                                    'name': home_address['location']['name'],
                                                    'type': 1
                                                    },
                                                "type": 1
                                                }
                                            ]
                                        }
                                        print_json(existing_address)
                                        break
                                    # else:
                                    #     existing_address = {
                                    #         'addresses': [
                                    #             {
                                    #                 'line1': home_address['line1'],
                                    #                 'zip_code': home_address['zip_code'],
                                    #                 'location': {
                                    #                     'name': home_address['location']['name'],
                                    #                     'type': 1
                                    #                     },
                                    #                 "type": 2
                                    #             }
                                    #         ]
                                    #     }
                                    #     print_json(existing_address)
                                    #     break
                            except:
                                pass
                                    
                        if int(ab_address_number) == 1:
                            try:
                                for home_address in ab_api_response_address['addresses']:
                                    print("Getting existing office address")
                                    if home_address['type'] == 2:
                                        existing_address = {
                                            'addresses': [
                                                {
                                                    'line1': home_address['line1'],
                                                    'zip_code': home_address['zip_code'],
                                                    'location': {
                                                        'name': home_address['location']['name'],
                                                        'type': 1
                                                        },
                                                    "type": 2
                                                }
                                            ]
                                        }
                                        print_json(existing_address)
                                        break
                                    # else:
                                    #     existing_address = {
                                    #         'addresses': [
                                    #             {
                                    #                 'line1': home_address['line1'],
                                    #             'zip_code': home_address['zip_code'],
                                    #             'location': {
                                    #                 'name': home_address['location']['name'],
                                    #                 'type': 1
                                    #                 },
                                    #             "type": 1
                                    #             }
                                    #         ]
                                    #     }
                                    #     print_json(existing_address)
                                    #     break
                            except:
                                pass
                                        
                        new_address = {
                            'addresses': [
                                {
                                    'line1': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, ""),
                                    'zip_code': zip,
                                    'location': {
                                        'name': city + ", " + state + ", " + country,
                                        "type": ab_address_number
                                    },
                                    "type": ab_address_number
                                }
                            ]
                        }
                        
                        print("New Address")
                        print_json(new_address)
                        
                        print("Existing Address")
                        print_json(existing_address)
                        
                        params_address = []
                        for each_address in existing_address['addresses']:
                            params_address.append(each_address)
                            
                        for each_address in new_address['addresses']:
                            params_address.append(each_address)
                            
                        params = {
                            'addresses': params_address
                        }
                        
                        print_json(params)
                        
                    # Will add as custom field - permanent address   
                    if int(ab_address_number) == 3:
                        print("Will add the new location as custom field - permanent address")  
                        
                        params = {
                            'custom_fields': {
                                'permanent_address': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, "")
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'permanent_city': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': city
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'permanent_state': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': state
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'permanent_country': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': country
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'permanent_postal_code': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': zip
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                }
                            }
                        }
                    
                    # Will add as address
                    if int(ab_address_number) == 4:
                        print("Will add the new location as Address")
                        
                        print("Will add the new location as custom field - work address")  
                        params = {
                            'custom_fields': {
                                'work_address_line_1': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': address.replace("  ", " ").replace(" " + city + " " + state + " " + country, "").replace(zip, "")
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'work_city': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': city
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'work_state': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': state
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'work_country': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': country
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                },
                                'work_postal_code': {
                                    'values': [
                                        {
                                            'value': {
                                                'content': zip
                                            },
                                            'display_order': 0
                                        }
                                    ]
                                }
                            }
                        }
                    
                    print("I am going with Address No.: " + str(ab_address_number))
                    patch_request_ab()
                    print(ab_api_response)
                    
                    # Will update in PostgreSQL
                    insert_updates = """
                                    INSERT INTO ab_address_added (ab_system_id, address, date)
                                    VALUES (%s, %s, now())
                                    """
                    cur.execute(insert_updates, [ab_system_id, address])
                    conn.commit()
                    print("Added the missing address in Almabase")
                    
                    # Remove the slot from the available ones
                    print("Removing the address slot from the available ones")
                    consumed_slot.append(ab_address_number)
                    available_slots = set(almabase_slots) - set(consumed_slot)
                    
                    print("Available address slots: " + str(available_slots))
                        
                    # Remove the address from the missing ones
                    print("Removing the address from the missing ones")
                    updated_address.append(address)
                    new_missing_in_ab = set(missing_in_ab) - set(updated_address)
                    missing_in_ab = new_missing_in_ab
                    
                    print("Yet to be added address in AB: " + str(missing_in_ab))
                break
            
    # Retrieve IITB education from RE
    print("Retrieving IITB education details from RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/educations" % re_system_id
    params = {}
    get_request_re()

    re_api_response_education_all = re_api_response

    i = 0
    re_api_response_education = {
        'value': [
            
        ]
    }

    for each_education in re_api_response['value']:
        if each_education['school'] == "Indian Institute of Technology Bombay":
            re_api_response_education['value'].append(each_education)

    # Retrieve IITB education from AlmaBase
    print("Retrieving IITB education details from Almabase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s/educations" % ab_system_id

    get_request_almabase()
    ab_api_response_education = ab_api_response

    # Compare the ones present in RE with AlmaBase and find delta
    print("Comparing the education details present in RE with AlmaBase and find delta")
    # When only one education exists in both
    if len(re_api_response_education['value']) == 1 and ab_api_response_education['count'] == 1:
        print("Only one education record exist in RE")
        
        # Get data from RE
        try:
            re_class_of = re_api_response_education['value'][0]['class_of']
            
            if int(re_class_of) < 1962:
                re_class_of = ""
        except:
            re_class_of = ""
            
        try:
            re_department = re_api_response_education['value'][0]['majors'][0]
        except:
            re_department = ""
            
        try:
            re_degree = re_api_response_education['value'][0]['degree']
        except:
            re_degree = ""
            
        try:
            re_hostel = re_api_response_education['value'][0]['social_organization']
        except:
            re_hostel = ""
            
        try:
            re_joining_year = re_api_response_education['value'][0]['date_entered']['y']
        except:
            re_joining_year = ""
            
        try:
            re_roll_number = re_api_response_education['value'][0]['known_name']
        except:
            re_roll_number = ""
            
        re_education_id = re_api_response_education['value'][0]['id']
            
        # Get data from AlmaBase
        print("Getting the corresponding education details from Almabase")
        try:
            ab_class_of = ab_api_response_education['results'][0]['class_year']
            
            if int(ab_class_of) < 1962 or ab_class_of == "null" or ab_class_of is None:
                ab_class_of = ""
        except:
            ab_class_of = ""
            
        try:
            ab_department = ab_api_response_education['results'][0]['branch']['name']
            
            if ab_department == "null" or ab_department is None or ab_department == "Other" or ab_department.strip() == "Other":
                ab_department = ""
        except:
            ab_department = ""
            
        try:
            ab_degree = ab_api_response_education['results'][0]['course']['name']
            print(ab_degree)
            
            if ab_degree == "Other" or ab_degree == "null" or ab_degree is None or ab_degree.strip() == "Other":
                print("Convering Other to blank")
                ab_degree = ""
            
        except:
            ab_degree = ""
            
        print(ab_degree)
            
        try:
            ab_hostel = ab_api_response_education['results'][0]['custom_fields']['hostel']['values'][0]['value']['label']
            
            if ab_hostel == "Other" or ab_hostel == "null" or ab_hostel is None or ab_hostel.strip() == "Other":
                ab_hostel = ""
        except:
            ab_hostel = ""
        
        try:
            ab_joining_year = ab_api_response_education['results'][0]['year_of_joining']
            
            if ab_joining_year == "null" or ab_joining_year is None:
                ab_joining_year = ""
        except:
            ab_joining_year = ""
            
        try:
            ab_roll_number = ab_api_response_education['results'][0]['roll_number']
            
            if ab_roll_number == "null" or ab_roll_number is None:
                ab_roll_number = ""
        except:
            ab_roll_number = ""
            
        ab_education_id = ab_api_response_education['results'][0]['id']
        
        # Upload the delta to RE
        if re_class_of == "" or re_department == "" or re_degree == "" or re_hostel == "" or re_joining_year == "" or re_roll_number == "":
            print("Uploading the delta in RE")
            
            if re_class_of == "" and ab_class_of != "":
                re_class_of = ab_class_of
                re_graduation_status = "Graduated"
            else:
                re_class_of = ""
                re_graduation_status = ""
                
            if re_department == "" or re_department == "Other" and ab_department != "":
                extract_department = """
                SELECT re_department FROM department_mapping WHERE ab_department = '%s' FETCH FIRST 1 ROW ONLY;
                """
                cur.execute(extract_sql, [ab_department])
                result = cur.fetchone()
                
                # Ensure no comma or brackets in output
                re_department = result[0]
            else:
                re_department = ""
                
            if re_degree == "" or re_degree == "Other" and ab_degree != "":
                extract_degree = """
                SELECT re_degree FROM degree_mapping WHERE ab_degree = '%s' FETCH FIRST 1 ROW ONLY;
                """
                cur.execute(extract_degree, [ab_degree])
                result = cur.fetchone()
                
                # Ensure no comma or brackets in output
                re_degree = result[0]
            else:
                re_degree = ""
                
            if re_hostel == "" or re_hostel == "Other" and ab_hostel != "":
                re_hostel = ab_hostel
            else:
                re_hostel = ""
            
            if re_joining_year == "" and ab_joining_year != "":
                re_joining_year = ab_joining_year
            else:
                re_joining_year = ""
                
            if re_roll_number == "" and ab_roll_number != "":
                re_roll_number = ab_roll_number
            else:
                re_roll_number = ""
            
            params_re = {
                'known_name': re_roll_number,
                'class_of': re_class_of,
                'date_entered': {
                    'y': re_joining_year
                },
                'date_graduated': {
                    'y': re_class_of
                },
                'date_left': {
                    'y': re_class_of
                },
                'degree': re_degree,
                'majors': [
                    re_department
                ],
                'social_organization': re_hostel,
                'status': re_graduation_status,
            }
            
            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params_re.copy())
                
            print_json(params)
                
            if params != {}:
                url = f"https://api.sky.blackbaud.com/constituent/v1/educations/{re_education_id}"
                patch_request_re()
                
                check_for_errors()
                
                # Adding Update Tags
                add_tags('education', params)
                
                print(re_api_response)
                
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_iitb_education_added (re_system_id, roll_number, department, joining_year, class_of, degree, hostel, date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                            """
            cur.execute(insert_updates, [re_system_id, re_roll_number, re_department, re_joining_year, re_class_of, re_degree, re_hostel])
            conn.commit()
            print("Added missing education details in RE")
        
        # Compare the ones present in AlmaBase with RE and find delta
        if ab_class_of == "" or ab_department == "" or ab_degree == "" or ab_hostel == "" or ab_joining_year == "" or ab_roll_number == "":
            if re_class_of != "" and ab_class_of == "":
                ab_class_of = re_class_of
                
            if re_department != "" and ab_department == "":
                extract_department = """
                SELECT ab_department FROM department_mapping WHERE re_department = '%s' FETCH FIRST 1 ROW ONLY;
                """
                cur.execute(extract_sql, [re_department])
                result = cur.fetchone()
                
                # Ensure no comma or brackets in output
                ab_department = result[0]
                
            if re_degree != "" and ab_degree == "":
                extract_degree = """
                SELECT ab_degree FROM degree_mapping WHERE re_degree = '%s' FETCH FIRST 1 ROW ONLY;
                """
                cur.execute(extract_degree, [re_degree])
                result = cur.fetchone()
                
                # Ensure no comma or brackets in output
                ab_degree = result[0]
                
            if re_hostel != "" and ab_hostel == "":
                # Taking the last Hostel after comma
                ab_hostel = re_hostel[re_hostel.rfind(",") +1:].lower().replace(" ","_")
            else:
                ab_hostel_content = ab_hostel.lower().replace(" ","_")
                ab_hostel = ab_hostel_content
                
            if re_joining_year != "" and ab_joining_year == "":
                ab_joining_year = re_joining_year
                
            if re_roll_number != "" and ab_roll_number == "":
                    ab_roll_number = re_roll_number
                
            params_ab = {
                'course': {
                    'name': ab_degree
                    },
                'branch': {
                    'name': ab_department
                    },
                'custom_fields': {
                    'hostel': {
                        'values': [
                            {
                                'value': {
                                    'content': ab_hostel
                                },
                                'display_order': 0
                            }
                        ],
                        'label': 'Hostel'
                    }
                },
                'year_of_graduation': ab_class_of,
                'year_of_joining': ab_joining_year,
                'year_of_leaving': ab_class_of,
                'roll_number': ab_roll_number,
                'college': {
                    'name': 'IIT Bombay'
                }
            }
            
            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params_ab.copy())
                
            print_json(params)
            
            if params != {} and ab_class_of != "":
                url = f"https://api.almabaseapp.com/api/profiles/{ab_system_id}/educations/{ab_education_id}"
                print(url)
                patch_request_ab()
                print(ab_api_response)
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO ab_iitb_education_added (ab_system_id, roll_number, department, joining_year, class_of, degree, hostel, date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                                """
                cur.execute(insert_updates, [ab_system_id, ab_roll_number, ab_department, ab_joining_year, ab_class_of, ab_degree, ab_hostel])
                conn.commit()
                print("Added missing education details in Almabase")
        
    # When more than one exists
    else:
        print("Multiple IITB education exists in RE")
        subject = "Multiple IITB Education details exists in either Raisers Edge or AlmaBase for syncing"
        multiple_education_exists()

    # Get other education details from RE
    print("Getting other education details from RE")
    re_other_school_name_list = []

    for each_education in re_api_response_org['value']:
        try:
            if each_education['reciprocal_type'] == 'Student':
                # Retrieve the University name
                re_other_school_name_list.append(each_education['name'])
        except:
            pass

    for each_education in re_api_response_education_all['value']:
        try:
            if each_education['school'] != 'Indian Institute of Technology Bombay':
                # Retrieve the University name
                re_other_school_name_list.append(each_education['school'])
        except:
            pass

    # Get other education details from AlmaBase
    print("Getting other education details from AlmaBase")
    ab_other_school_name_list = []

    url  = "https://api.almabaseapp.com/api/v1/profiles/%s/other_educations" % ab_system_id
    get_request_almabase()

    try:
        for each_education in ab_api_response['results']:
            try:
                ab_other_school_name_list.append(each_education['college']['name'])
            except:
                pass
    except:
        pass

    # Finding missing other schools to be added in Raisers Edge
    print("Finding missing other schools to be added in Raisers Edge")
    missing_in_re = []
    for each_school in ab_other_school_name_list:
        try:
            likely_school, score = process.extractOne(each_school, re_other_school_name_list)
            if score < 80:
                missing_in_re.append(each_school)
        except:
            missing_in_re.append(each_school)
    print("Missing schools in RE: " + str(missing_in_re))
            
    # Add missing records in RE
    if missing_in_re != []:
        print("Adding missing schools in RE")
        # Get from PostgreSQL
        extract_sql = """
                SELECT long_description FROM re_schools;
                """
        cur.execute(extract_sql)
        
        re_school_name_list = []
        for i in cur.fetchall():
            re_school_name_list.extend(i)
        
        for each_school in missing_in_re:

            try:
                likely_school, score = process.extractOne(each_school, re_school_name_list, score_cutoff = 85)
            except:
                likely_school = ""
            
            if likely_school != "":
                # Will add a new education in RE
                for ab_school in ab_api_response['results']:
                    try:
                        if each_school == ab_school['college']['name']:
                            
                            try:
                                class_of = ab_school['year_of_graduation']
                                if class_of == "" or class_of is None or class_of == "Null":
                                    class_of = ""
                            except:
                                class_of = ""
                                
                            try:
                                date_entered = ab_school['date_entered']
                                if date_entered == "" or date_entered is None or date_entered == "Null":
                                    date_entered = ""
                            except:
                                date_entered = ""
                            
                            try:
                                degree = ab_school['degree']['name']
                                if degree == "" or degree is None or degree == "Null":
                                    degree = ""
                            except:
                                degree = ""
                            
                            if degree != "":
                                extract_sql = """
                                            SELECT long_description FROM re_degrees;
                                            """
                                cur.execute(extract_sql)
                                
                                re_degree_name_list = []
                                
                                for i in cur.fetchall():
                                    re_degree_name_list.extend(i)
                                
                                try:
                                    likely_degree, score = process.extractOne(degree, re_degree_name_list, score_cutoff = 90)
                                except:
                                    likely_degree = ""

                                if likely_degree != "":
                                    degree = likely_degree.replace(",", ";")
                                else:
                                    try:
                                        params = {
                                            'long_description': degree
                                        }
                                        
                                        url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/6/tableentries"
                                        
                                        post_request_re()
                                        
                                        # Will update in PostgreSQL
                                        insert_updates = """
                                                        INSERT INTO re_degrees (long_description)
                                                        VALUES (%s)
                                                        """
                                        cur.execute(insert_updates, [degree.replace(";", ",")])
                                        conn.commit()
                                    except:
                                        degree = ""
                            
                            try:
                                department = ab_school['field_of_study']['name']
                                if department == "" or department is None or department == "Null":
                                    department = ""
                            except:
                                department = ""
                                
                            if department != "":
                                extract_sql = """
                                            SELECT long_description FROM re_departments;
                                            """
                                cur.execute(extract_sql)
                                
                                re_department_name_list = []
                                
                                for i in cur.fetchall():
                                    re_department_name_list.extend(i)
                                
                                try:
                                    likely_department, score = process.extractOne(department, re_department_name_list, score_cutoff = 90)
                                except:
                                    likely_department = ""

                                if likely_department != "":
                                    department = likely_department.replace(",", ";")
                                else:
                                    try:
                                        params = {
                                            'long_description': department
                                        }
                                        
                                        url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/1022/tableentries"
                                        
                                        post_request_re()
                                        
                                        # Will update in PostgreSQL
                                        insert_updates = """
                                                        INSERT INTO re_departments (long_description)
                                                        VALUES (%s)
                                                        """
                                        cur.execute(insert_updates, [department.replace(";", ",")])
                                        conn.commit()
                                    except:
                                        degree = ""
                                
                            break
                    except:
                        each_school = ""
                        class_of = ""
                        date_entered = ""
                        degree = ""
                        department = ""
                
                params_re = {
                    'constituent_id': re_system_id,
                    'school': likely_school,
                    'class_of': class_of,
                    'date_graduated': {
                        'y': class_of
                    },
                    'date_left': {
                        'y': class_of
                    },
                    'date_entered': date_entered,
                    'degree': degree,
                    'campus': department[:50]
                }
                
                # Delete blank values from JSON
                for i in range(10):
                    params = del_blank_values_in_json(params_re.copy())
                
                url = "https://api.sky.blackbaud.com/constituent/v1/educations"
                post_request_re()
                
                check_for_errors()
            
                # Adding Update Tags
                add_tags('education', params)
                
                print(re_api_response)
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO re_other_education_added (re_system_id, school_name, date)
                                VALUES (%s, %s, now())
                                """
                cur.execute(insert_updates, [re_system_id, likely_school])
                conn.commit()
                print("Updated (other) education details in RE")
            else:
                # Will add a new school in RE
                print("Adding a new (other) school in RE")

                params = {
                    'long_description': each_school
                }
                
                url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/1022/tableentries"
                
                post_request_re()
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO re_schools (long_description)
                                VALUES (%s)
                                """
                cur.execute(insert_updates, [each_school.replace(";", ",")])
                conn.commit()
                
                # Will add a new education in RE
                for ab_school in ab_api_response['results']:
                    try:
                        if each_school == ab_school['college']['name']:
                            
                            try:
                                class_of = ab_school['year_of_graduation']
                                if class_of == "" or class_of is None or class_of == "Null":
                                    class_of = ""
                            except:
                                class_of = ""
                                
                            try:
                                date_entered = ab_school['date_entered']
                                if date_entered == "" or date_entered is None or date_entered == "Null":
                                    date_entered = ""
                            except:
                                date_entered = ""
                            
                            try:
                                degree = ab_school['degree']['name']
                                if degree == "" or degree is None or degree == "Null":
                                    degree = ""
                            except:
                                degree = ""
                            
                            if degree != "":
                                extract_sql = """
                                            SELECT long_description FROM re_degrees;
                                            """
                                cur.execute(extract_sql)
                                
                                re_degree_name_list = []
                                
                                for i in cur.fetchall():
                                    re_degree_name_list.extend(i)
                                
                                try:
                                    likely_degree, score = process.extractOne(degree, re_degree_name_list, score_cutoff = 90)
                                except:
                                    likely_degree = ""

                                if likely_degree != "":
                                    degree = likely_degree.replace(",", ";")
                                else:
                                    try:
                                        params = {
                                            'long_description': degree
                                        }
                                        
                                        url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/6/tableentries"
                                        
                                        post_request_re()
                                        
                                        # Will update in PostgreSQL
                                        insert_updates = """
                                                        INSERT INTO re_degrees (long_description)
                                                        VALUES (%s)
                                                        """
                                        cur.execute(insert_updates, [degree.replace(";", ",")])
                                        conn.commit()
                                    except:
                                        degree = ""
                            
                            try:
                                department = ab_school['field_of_study']['name']
                                if department == "" or department is None or department == "Null":
                                    department = ""
                            except:
                                department = ""
                                
                            if department != "":
                                extract_sql = """
                                            SELECT long_description FROM re_departments;
                                            """
                                cur.execute(extract_sql)
                                
                                re_department_name_list = []
                                
                                for i in cur.fetchall():
                                    re_department_name_list.extend(i)
                                
                                try:
                                    likely_department, score = process.extractOne(department, re_department_name_list, score_cutoff = 90)
                                except:
                                    likely_department = ""

                                if likely_department != "":
                                    department = likely_department.replace(",", ";")
                                else:
                                    try:
                                        params = {
                                            'long_description': department
                                        }
                                        
                                        url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/1022/tableentries"
                                        
                                        post_request_re()
                                        
                                        # Will update in PostgreSQL
                                        insert_updates = """
                                                        INSERT INTO re_departments (long_description)
                                                        VALUES (%s)
                                                        """
                                        cur.execute(insert_updates, [department.replace(";", ",")])
                                        conn.commit()
                                    except:
                                        degree = ""
                                
                            break
                    except:
                        each_school = ""
                        class_of = ""
                        date_entered = ""
                        degree = ""
                        department = ""
            
                params_re = {
                    'constituent_id': re_system_id,
                    'school': likely_school,
                    'class_of': class_of,
                    'date_graduated': {
                        'y': class_of
                    },
                    'date_left': {
                        'y': class_of
                    },
                    'date_entered': date_entered,
                    'degree': degree,
                    'campus': department[:50]
                }
                
                # Delete blank values from JSON
                for i in range(10):
                    params = del_blank_values_in_json(params_re.copy())
                
                url = "https://api.sky.blackbaud.com/constituent/v1/educations"
                post_request_re()
                
                check_for_errors()
        
                # Adding Update Tags
                add_tags('education', params)
                
                print(re_api_response)
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO re_other_education_added (re_system_id, school_name, date)
                                VALUES (%s, %s, now())
                                """
                cur.execute(insert_updates, [re_system_id, likely_school])
                conn.commit()
                print("Added a new (other) education in RE")

    # Finding missing other schools to be added in AlmaBase
    print("Finding missing other schools to be added in AlmaBase")
    missing_in_ab = []
    for each_school in re_other_school_name_list:
        try:
            likely_phone, score = process.extractOne(each_school, ab_other_school_name_list)
            if score < 80:
                missing_in_ab.append(each_school)
        except:
            missing_in_ab.append(each_school)

    if missing_in_ab != []:
        for each_school in missing_in_ab:
            for each_education in re_api_response_org['value']:
                try:
                    i = 0
                    if each_education['name'] == each_school:
                        
                        try:
                            year_of_graduation = each_education['end']['y']
                            if year_of_graduation == "" or year_of_graduation is None or year_of_graduation == "Null":
                                year_of_graduation = ""
                        except:
                            year_of_graduation = ""
                        
                        try:
                            year_of_joining = each_education['start']['y']
                            if year_of_joining == "" or year_of_joining is None or year_of_joining == "Null":
                                year_of_joining = ""
                        except:
                            year_of_joining = ""
                            
                        try:
                            course = each_education['position']
                            if course == "" or course is None or course == "Null":
                                course = ""
                        except:
                            course = ""
                        i = 1
                        
                        department = ""
                        
                        break
                except:
                    pass
                
            if i == 0:
                for each_education in re_api_response_education_all['value']:
                    try:
                        if each_education['school'] == each_school:
                            
                            try:
                                year_of_graduation = each_education['class_of']
                                if year_of_graduation == "" or year_of_graduation is None or year_of_graduation == "Null":
                                    year_of_graduation = ""
                            except:
                                year_of_graduation = ""
                                
                            try:
                                year_of_joining = each_education['date_entered']['y']
                                if year_of_joining == "" or year_of_joining is None or year_of_joining == "Null":
                                    year_of_joining = ""
                            except:
                                year_of_joining = ""
                            
                            try:
                                course = each_education['degree']
                                if course == "" or course is None or course == "Null":
                                    course = ""
                            except:
                                course = ""
                                
                            try:
                                department = each_education['campus']
                                if department == "" or department is None or department == "Null":
                                    department = ""
                            except:
                                department = ""
                                
                            break
                    except:
                        pass
            
            params_ab = {
                'college': {
                    'name': each_school
                },
                'course': {
                    'name': course
                },
                'branch': {
                    'name': department
                },
                'year_of_graduation': year_of_graduation,
                'year_of_joining': year_of_joining
            }
            
            # Delete blank values from JSON
            for i in range(10):
                params = del_blank_values_in_json(params_ab.copy())
            
            url = "https://api.almabaseapp.com/api/v1/profiles/%s/other_educations" % ab_system_id
            post_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_other_education_added (ab_system_id, school_name, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [ab_system_id, each_school])
            conn.commit()
            print("Added (other) education details in Almabase")

    # Sync Generic person Details
    print("Syncing Generic details...")
    # Get personal details from RE
    print("Getting personal details from RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s" % re_system_id
    params = {}
    get_request_re()
    re_api_response_generic_details = re_api_response

    try:
        re_gender = re_api_response_generic_details['gender']
        if re_gender is None or re_gender =="Null" or re_gender == "null":
            re_gender = ""
    except:
        re_gender = ""

    try:
        re_dob_day = re_api_response_generic_details['birthdate']['d']
        if re_dob_day is None or re_dob_day =="Null" or re_dob_day == "null":
            re_dob_day = ""
    except:
        re_dob_day = ""
        
    try:
        re_dob_month = re_api_response_generic_details['birthdate']['m']
        if re_dob_month is None or re_dob_month =="Null" or re_dob_month == "null":
            re_dob_month = ""
    except:
        re_dob_month = ""
        
    try:
        re_dob_year = re_api_response_generic_details['birthdate']['y']
        if re_dob_year is None or re_dob_year =="Null" or re_dob_year == "null":
            re_dob_year = ""
    except:
        re_dob_year = ""
        
    re_dob = str(re_dob_year) + "-" + str(re_dob_month) + "-" + str(re_dob_day)

    try:
        re_first_name = re_api_response_generic_details['first']
        if re_first_name is None or re_first_name =="Null" or re_first_name == "null":
            re_first_name = ""
    except:
        re_first_name = ""
        
    try:
        re_middle_name = re_api_response_generic_details['middle']
        if re_middle_name is None or re_middle_name =="Null" or re_middle_name == "null":
            re_middle_name = ""
    except:
        re_middle_name = ""
        
    try:
        re_last_name = re_api_response_generic_details['last']
        if re_last_name is None or re_last_name =="Null" or re_last_name == "null":
            re_last_name = ""
    except:
        re_last_name = ""

    re_full_name = (re_first_name + " " + re_middle_name + " " + re_last_name).replace(".", " ").replace("  ", " ")

    try:
        re_deceased = re_api_response_generic_details['deceased']
        if re_deceased is None or re_deceased =="Null" or re_deceased == "null":
            re_deceased = ""
    except:
        re_deceased = ""

    # Get personal details from Almabase
    print("Getting personal details from Almabase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
    get_request_almabase()

    ab_api_response_generic_details = ab_api_response

    try:
        ab_gender = ab_api_response_generic_details['gender']
        if ab_gender is None or ab_gender =="Null" or ab_gender == "null":
            ab_gender = ""
    except:
        ab_gender = ""

    try:
        ab_dob = ab_api_response_generic_details['date_of_birth']
        if ab_dob is None or ab_dob =="Null" or ab_dob == "null":
            ab_dob = ""
            ab_dob_day = ""
            ab_dob_month = ""
            ab_dob_year = ""
        else:
            date_time_obj = datetime.strptime(ab_dob, '%Y-%m-%d')
            ab_dob_day = date_time_obj.day
            ab_dob_month = date_time_obj.month 
            ab_dob_year = date_time_obj.year
    except:
        ab_dob = ""
        ab_dob_day = ""
        ab_dob_month = ""
        ab_dob_year = ""

    try:
        ab_first_name = ab_api_response_generic_details['first_name']
        if ab_first_name is None or ab_first_name =="Null" or ab_first_name == "null":
            ab_first_name = ""
    except:
        ab_first_name = ""

    try:
        ab_middle_name = ab_api_response_generic_details['middle_name']
        if ab_middle_name is None or ab_middle_name =="Null" or ab_middle_name == "null":
            ab_middle_name = ""
    except:
        ab_middle_name = ""

    try:
        ab_last_name = ab_api_response_generic_details['last_name']
        if ab_last_name is None or ab_last_name =="Null" or ab_last_name == "null":
            ab_last_name = ""
    except:
        ab_last_name = ""

    ab_full_name = (ab_first_name + " " + ab_middle_name + " " + ab_last_name).replace("  ", " ")

    try:
        ab_deceased = ab_api_response_generic_details['deceased']
        if ab_deceased is None or ab_deceased =="Null" or ab_deceased == "null":
            ab_deceased = ""
    except:
        ab_deceased = ""
        
    try:
        ab_nickname = ab_api_response_generic_details['nick_name']
        if ab_nickname is None or ab_nickname =="Null" or ab_nickname == "null":
            ab_nickname = ""
    except:
        ab_nickname = ""

    # Compare RE with AB
    print('Comparing personal details of RE with Almabase')
    re_gender_update = ""
    if re_gender == "" or re_gender == "Unknown" and ab_gender != "":
        re_gender_update = ab_gender
    elif re_gender == "" or re_gender == "Unknown" and ab_gender == "":
        if re_first_name != "" and len(re_first_name) <= 2:
            url = "https://api.genderize.io?name=%s" % re_first_name
            response = http.get(url)
            json_response = response.json()
            re_gender_update = json_response['gender'].title()
        else:
            re_gender_update = "Male"

    if re_dob_day == "" and re_dob_month == "" and re_dob_year == "":
        re_dob_day_update = ab_dob_day
        re_dob_month_update = ab_dob_month 
        re_dob_year_update = ab_dob_year
    else:
        re_dob_day_update = ""
        re_dob_month_update = "" 
        re_dob_year_update = ""

    if len(re_first_name) < len(ab_first_name) or re_first_name == ".":
        re_first_name_update = ab_first_name.title()
    else:
        re_first_name_update = ""

    if len(re_middle_name) < len(ab_middle_name) or re_middle_name == ".":
        re_middle_name_update = ab_middle_name.title()
    else:
        re_middle_name_update = ""

    if len(re_last_name) < len(ab_last_name) or re_last_name == ".":
        re_last_name_update = ab_last_name.title()
    else:
        re_last_name_update = ""

    re_former_name_update = ""
    if re_first_name_update != "" or re_middle_name_update != "" or re_last_name_update != "":
        if len(re_full_name) > len(ab_full_name):
            re_first_name_update = ""
            re_middle_name_update = ""
            re_last_name_update = ""
            re_former_name_update = ""
        else:
            re_former_name_update = re_full_name

    if re_deceased == "false" and ab_deceased == "true":
        re_deceased_update = "true"
    else:
        re_deceased_update = ""

    re_preferred_name_update = ab_nickname

    # Find delta and upload
    print("Finding delta for personal data and uploading in RE")
    params_re = {
        'birthdate': {
            'd': re_dob_day_update,
            'm': re_dob_month_update,
            'y': re_dob_year_update
        },
        'deceased': re_deceased_update,
        'first': re_first_name_update,
        'former_name': re_former_name_update,
        'gender': re_gender_update,
        'last': re_last_name_update,
        'middle': re_middle_name_update,
        'preferred_name': re_preferred_name_update[:50],
    }

    # Delete blank values from JSON
    for i in range(10):
        params = del_blank_values_in_json(params_re.copy())
        
    if params != {}:
        url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s" % re_system_id
        patch_request_re()
        
        check_for_errors()
                
        # Adding Update Tags
        add_tags('bio', params)
        
        print(re_api_response)
        
        # Will update in PostgreSQL
        insert_updates = """
                        INSERT INTO re_personal_details_added (re_system_id, birth_day, birth_month, birth_year, deceased, first_name, former_name, gender, last_name, middle_name, preferred_name, date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                        """
        cur.execute(insert_updates, [re_system_id, re_dob_day_update, re_dob_month_update, re_dob_year_update, re_deceased_update, re_first_name_update, re_former_name_update, re_gender_update, re_last_name_update, re_middle_name_update, re_preferred_name_update])
        conn.commit()
        print("Updated personal details in RE")

    # Compare AB with RE
    print("Comparing the personal details to upload in AlmaBase")
    ab_gender_update = ""
    if re_gender != "" and ab_gender == "":
        ab_gender_update = re_gender
    elif re_gender == "" and ab_gender == "":
        ab_gender_update = re_gender_update

    ab_dob_update = ""
    if ab_dob_day == "" and ab_dob_month == "" and ab_dob_year == "":
        if re_dob_day != "" and re_dob_month != "" and re_dob_year != "":
            ab_dob_update = datetime(re_dob_year, re_dob_month, re_dob_day).date()
        elif re_dob_day != "" and re_dob_month != "":
            ab_dob_update = str(re_dob_month) + "-" + str(re_dob_day)
    else:
        ab_dob_update = ""
        
    if len(re_first_name) > len(ab_first_name) or ab_first_name == ".":
        ab_first_name_update = re_first_name.title()
    else:
        ab_first_name_update = ""
        
    if len(re_middle_name) > len(ab_middle_name) or ab_middle_name == ".":
        ab_middle_name_update = re_middle_name.title()
    else:
        ab_middle_name_update = ""
        
    if len(re_last_name) > len(ab_last_name) or ab_last_name == ".":
        ab_last_name_update = re_last_name.title()
    else:
        ab_last_name_update = ""
        
    if re_deceased == "true" and ab_deceased == "false":
        ab_deceased_update = "true"
    else:
        ab_deceased_update = ""

    # Find delta and upload
    print("Finding delta to upload in Almabase")
    params_ab = {
        'first_name': ab_first_name_update,
        'middle_name': ab_middle_name_update,
        'last_name': ab_last_name_update,
        'gender': ab_gender_update,
        'date_of_birth': ab_dob_update,
        'deceased': ab_deceased_update
    }

    # Delete blank values from JSON
    for i in range(10):
        params = del_blank_values_in_json(params_ab.copy())
        
    if params != {}:
        print("Uploading delta of personal details in Almabase")
        url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
        patch_request_ab()
        
        # Will update in PostgreSQL
        insert_updates = """
                        INSERT INTO ab_personal_details_added (ab_system_id, first_name, middle_name, last_name, gender, dob, deceased, date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                        """
        cur.execute(insert_updates, [ab_system_id, ab_first_name_update, ab_middle_name_update, ab_last_name_update, ab_gender_update, ab_dob_update, ab_deceased_update])
        conn.commit()
        print("Uploaded delta of personal details in Almabase")
        
    # Sync Social media details
    print("Syncing Social Media details")
    # Get social media details from RE
    print("Getting social media details from RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/onlinepresences" % re_system_id
    params = {}
    get_request_re()
    re_api_response_social = re_api_response

    website_re = ""
    linkedin_re = ""
    facebook_re = ""
    twitter_re = ""
    google_re = ""

    for each_social in re_api_response_social['value']:
        try:
            # Get Website
            print("Checking website")
            try:
                if each_social['type'] == "Website":
                    website_re = each_social['address']
                    
                    if website_re is None or website_re == "Null" or website_re == "null":
                        website_re = ""
            except:
                website_re = ""
            
            # Get LinkedIn
            print("Checing LinkedIn")
            try:
                if each_social['type'] == "LinkedIn":
                    linkedin_re = each_social['address']
                    
                    if linkedin_re is None or linkedin_re == "Null" or linkedin_re == "null":
                        linkedin_re = ""
            except:
                linkedin_re = ""

            # Get Facebook
            print("Checing Facebook")
            try:
                if each_social['type'] == "Facebook":
                    facebook_re = each_social['address']
                    
                    if facebook_re is None or facebook_re == "Null" or facebook_re == "null":
                        facebook_re = ""
            except:
                facebook_re = ""
            
            # Get Twitter
            print("Checing Twitter")
            try:
                if each_social['type'] == "Twitter":
                    twitter_re = each_social['address']
                    
                    if twitter_re is None or twitter_re == "Null" or twitter_re == "null":
                        twitter_re = ""
            except:
                twitter_re = ""
            
            # Get Google
            print("Checing Google")
            try:
                if each_social['type'] == "Google":
                    google_re = each_social['address']
                    
                    if google_re is None or google_re == "Null" or google_re == "null":
                        google_re = ""
            except:
                google_re = ""
        except:
            website_re = ""
            linkedin_re = ""
            facebook_re = ""
            twitter_re = ""
            google_re = ""

    if website_re != "":
        re_website = "https://" + website_re.replace("https://", "").replace("http://", "")
        website_re = re_website
    else:
        re_website = ""
        website_re = ""

    if linkedin_re != "":
        re_linkedin = "https://www." + linkedin_re.replace("https://www.", "").replace("www.", "").replace("http://", "")
        linkedin_re = re_linkedin
    else:
        re_linkedin = ""
        linkedin_re = ""

    if facebook_re != "":
        re_facebook = "https://www." + facebook_re.replace("https://www.", "").replace("www.", "").replace("http://", "")
        facebook_re = re_facebook
    else:
        re_facebook = ""
        facebook_re = ""

    if twitter_re != "":
        re_twitter = "https://www." + twitter_re.replace("https://www.", "").replace("www.", "").replace("http://", "").replace("@", "twitter.com/")
        twitter_re = re_twitter
    else:
        re_twitter = ""
        twitter_re = ""

    if google_re != "":
        re_google = "https://www." + google_re.replace("https://www.", "").replace("www.", "").replace("http://", "")
        google_re = re_google
    else:
        re_google = ""
        google_re = ""

    # Get social media details from AB
    print("Getting social media details from Almabase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s/social_links" % ab_system_id
    get_request_almabase()
    ab_api_response_social = ab_api_response

    website_ab = ""
    linkedin_ab = ""
    facebook_ab = ""
    twitter_ab = ""
    google_ab = ""

    for each_social in ab_api_response_social['results']:
        try:
            # Get Website
            print("Checking Website")
            try:
                if each_social['type_display'] == "Website":
                    website_ab = each_social['link']
                    
                    if website_ab is None or website_ab == "Null" or website_ab == "null":
                        website_ab = ""
            except:
                website_ab = ""
            
            # Get LinkedIn
            print("Checking LinkedIn")
            try:
                if each_social['type_display'] == "LinkedIn":
                    linkedin = each_social['link']
                    
                    if linkedin_ab is None or linkedin_ab == "Null" or linkedin_ab == "null":
                        linkedin_ab = ""
            except:
                linkedin_ab = ""

            # Get Facebook
            print("Checking Facebook")
            try:
                if each_social['type_display'] == "Facebook":
                    facebook_ab = each_social['link']
                    
                    if facebook_ab is None or facebook_ab == "Null" or facebook_ab == "null":
                        facebook_ab = ""
            except:
                facebook_ab = ""
            
            # Get Twitter
            print("Checking Twitter")
            try:
                if each_social['type_display'] == "Twitter":
                    twitter_ab = each_social['link']

                    if twitter_ab is None or twitter_ab == "Null" or twitter_ab == "null":
                        twitter_ab = ""
            except:
                twitter_ab = ""
            
            # Get Google
            print("Checking Google")
            try:
                if each_social['type_display'] == "Google":
                    google_ab = each_social['link']
                    
                    if google_ab is None or google_ab == "Null" or google_ab == "null":
                        google_ab = ""
            except:
                google_ab = ""
        except:
            website_ab = ""
            linkedin_ab = ""
            facebook_ab = ""
            twitter_ab = ""
            google_ab = ""

    if website_ab != "":
        ab_website = website_ab.replace("https://", "").replace("http://", "")
        website_ab = ab_website
    else:
        ab_website = ""
        website_ab = ""

    if linkedin_ab != "":
        ab_linkedin = linkedin_ab.replace("https://www.", "").replace("www.", "").replace("http://", "")
        linkedin_ab = ab_linkedin
    else:
        ab_linkedin = ""
        linkedin_ab = ""

    if facebook_ab != "":
        ab_facebook = facebook_ab.replace("https://www.", "").replace("www.", "").replace("http://", "")
        facebook_ab = ab_facebook
    else:
        ab_facebook = ""
        facebook_ab = ""

    if twitter_ab != "":
        ab_twitter = "@" + twitter_ab.replace("https://www.", "").replace("www.", "").replace("http://", "").replace("twitter.com/", "")
        twitter_ab = ab_twitter
    else:
        ab_twitter = ""
        twitter_ab = ""

    if google_ab != "":
        ab_google = google_ab.replace("https://www.", "").replace("www.", "").replace("http://", "")
        google_ab = ab_google
    else:
        ab_google = ""
        google_ab = ""

    # Compare RE with AB
    print("Comparing RE details with Almabase")
    if re_website == "" and ab_website != "":
        re_website = ab_website
    else:
        re_website = ""

    if re_linkedin == "" and ab_linkedin != "":
        re_linkedin = ab_linkedin
    else:
        re_linkedin = ""

    if re_facebook == "" and ab_facebook != "":
        re_facebook = ab_facebook
    else:
        re_facebook = ""

    if re_twitter == "" and ab_twitter != "":
        re_twitter = ab_twitter
    else:
        re_twitter = ""

    if re_google == "" and ab_google != "":
        re_google = ab_google
    else:
        re_google = ""

    # Upload the delta to RE
    print("Uploading the missing social media details to RE")
    if re_website != "" or re_linkedin != "" or re_facebook != "" or re_twitter != "" or re_google != "":
        if re_website != "":
            print("Uploading Website in RE")
            params = {
                'address': re_website,
                'constituent_id': re_system_id,
                'type': 'Website'
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/onlinepresences"
            post_request_re()
            
            check_for_errors()
    
            # Adding Update Tags
            add_tags('online', f'Website: {re_website}')
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_social_media_added (re_system_id, address, type, date)
                            VALUES (%s, %s, 'Website', now())
                            """
            cur.execute(insert_updates, [re_system_id, re_website])
            conn.commit()
            
        if re_linkedin != "":
            print("Uploading LinkedIn in RE")
            params = {
                'address': re_linkedin,
                'constituent_id': re_system_id,
                'type': 'LinkedIn',
                'primary': 'true'
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/onlinepresences"
            post_request_re()
            
            check_for_errors()
    
            # Adding Update Tags
            add_tags('online', f'LinkedIn: {re_linkedin}')
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_social_media_added (re_system_id, address, type, date)
                            VALUES (%s, %s, 'LinkedIn', now())
                            """
            cur.execute(insert_updates, [re_system_id, re_linkedin])
            conn.commit()
            
        if re_facebook != "":
            print("Uploading Facebook in RE")
            params = {
                'address': re_facebook,
                'constituent_id': re_system_id,
                'type': 'Facebook'
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/onlinepresences"
            post_request_re()
            
            check_for_errors()
    
            # Adding Update Tags
            add_tags('online', f'Facebook: {re_facebook}')
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_social_media_added (re_system_id, address, type, date)
                            VALUES (%s, %s, 'Facebook', now())
                            """
            cur.execute(insert_updates, [re_system_id, re_facebook])
            conn.commit()
            
        if re_twitter != "":
            print("Uploading Twitter in RE")
            params = {
                'address': re_twitter,
                'constituent_id': re_system_id,
                'type': 'Twitter'
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/onlinepresences"
            post_request_re()
            
            check_for_errors()
    
            # Adding Update Tags
            add_tags('online', f'Twitter: {re_twitter}')
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_social_media_added (re_system_id, address, type, date)
                            VALUES (%s, %s, 'Twitter', now())
                            """
            cur.execute(insert_updates, [re_system_id, re_twitter])
            conn.commit()
        
        if re_google != "":
            print("Uploading Google in RE")
            params = {
                'address': re_google,
                'constituent_id': re_system_id,
                'type': 'Google'
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/onlinepresences"
            post_request_re()
            
            check_for_errors()
    
            # Adding Update Tags
            add_tags('online', f'Google: {re_google}')
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_social_media_added (re_system_id, address, type, date)
                            VALUES (%s, %s, 'Google', now())
                            """
            cur.execute(insert_updates, [re_system_id, re_google])
            conn.commit()
            
    # Compare AB with RE
    print("Comparing Social media details of Almabase with RE")
    if ab_website == "" and website_re != "":
        ab_website = website_re
    else:
        ab_website = ""

    if ab_linkedin == "" and linkedin_re != "":
        ab_linkedin = linkedin_re
    else:
        ab_linkedin = ""

    if ab_facebook == "" and facebook_re != "":
        ab_facebook = facebook_re
    else:
        ab_facebook = ""

    if ab_twitter == "" and twitter_re != "":
        ab_twitter = twitter_re
    else:
        ab_twitter = ""

    if ab_google == "" and google_re != "":
        ab_google = google_re
    else:
        ab_google = ""

    # Upload the delta to AB
    print("Uploading the missing social media details to Almabase")
    if ab_website != "" or ab_linkedin != "" or ab_facebook != "" or ab_twitter != "" or ab_google != "":
        if ab_website != "":
            print("Uploading Website in Almabase")
            params = {
                'link': ab_website,
                'type': 0
            }
            
            url = "https://api.almabaseapp.com/api/v1/profiles/%s/social_links" % ab_system_id
            post_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_social_media_added (ab_system_id, address, type, date)
                            VALUES (%s, %s, 'Website', now())
                            """
            cur.execute(insert_updates, [ab_system_id, ab_website])
            conn.commit()
            
        if ab_linkedin != "":
            print("Uploading LinkedIn in Almabase")
            params = {
                'link': ab_linkedin,
                'type': 1
            }
            
            url = "https://api.almabaseapp.com/api/v1/profiles/%s/social_links" % ab_system_id
            post_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_social_media_added (ab_system_id, address, type, date)
                            VALUES (%s, %s, 'LinkedIn', now())
                            """
            cur.execute(insert_updates, [ab_system_id, ab_linkedin])
            conn.commit()
            
        if ab_facebook != "":
            print("Uploading Facebook in Almabase")
            params = {
                'link': ab_facebook,
                'type': 2
            }
            
            url = "https://api.almabaseapp.com/api/v1/profiles/%s/social_links" % ab_system_id
            post_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_social_media_added (ab_system_id, address, type, date)
                            VALUES (%s, %s, 'Facebook', now())
                            """
            cur.execute(insert_updates, [ab_system_id, ab_facebook])
            conn.commit()
            
        if ab_twitter != "":
            print("Uploading Twitter in Almabase")
            params = {
                'link': ab_twitter,
                'type': 3
            }
            
            url = "https://api.almabaseapp.com/api/v1/profiles/%s/social_links" % ab_system_id
            post_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_social_media_added (ab_system_id, address, type, date)
                            VALUES (%s, %s, 'Twitter', now())
                            """
            cur.execute(insert_updates, [ab_system_id, ab_twitter])
            conn.commit()
            
        if ab_google != "":
            print("Uploading Google in Almabase")
            params = {
                'link': ab_google,
                'type': 4
            }
            
            url = "https://api.almabaseapp.com/api/v1/profiles/%s/social_links" % ab_system_id
            post_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_social_media_added (ab_system_id, address, type, date)
                            VALUES (%s, %s, 'Google', now())
                            """
            cur.execute(insert_updates, [ab_system_id, ab_google])
            conn.commit()

    # Sync interests
    print("Syncing interets")
    # Get interests from RE
    print("Getting interests from RE")
    url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/customfields" % re_system_id
    params = {}
    get_request_re()

    re_api_response_custom_fields = re_api_response

    re_interest_list = []
    for each_value in re_api_response['value']:
        try:
            if each_value['category'] == "Interests":
                re_interest_list.append(each_value['value'])
        except:
            pass

    # Get interests from AB
    print("Getting interests from Almabase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=interests" % ab_system_id
    get_request_almabase()

    ab_interest_list = []
    for each_value in ab_api_response['interests']:
        try:
            ab_interest_list.append(each_value['name'])
        except:
            pass

    # Compare interests between RE & AB
    print("Comparing interests between RE & Almabase")
    missing_in_re = []
    for each_interest in ab_interest_list:
        try:
            likely_interest, score = process.extractOne(each_interest, re_interest_list)
            if score < 80:
                missing_in_re.append(each_interest)
        except:
            missing_in_re.append(each_interest)
    print("Interests missing in RE: " + str(missing_in_re))

    # Upload delta to RE
    if missing_in_re != []:
        print("Uploading missing interests in RE")
        for each_interest in missing_in_re:
            params = {
                'category': 'Interests',
                'value': each_interest,
                'comment': 'Added from AlmaBase',
                'date': datetime.now().replace(microsecond=0).isoformat(),
                'parent_id': re_system_id
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/constituents/customfields"
            post_request_re()
            
            
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_interests_skills_added (re_system_id, value, type, date)
                            VALUES (%s, %s, 'Interests', now())
                            """
            cur.execute(insert_updates, [re_system_id, each_interest])
            conn.commit()
            print("Uploaded missing interests in RE")

    # Compare interests between AB & RE
    print("Compare interests between Almabase and RE")
    missing_in_ab_db = []
    for each_interest in re_interest_list:
        try:
            likely_interest, score = process.extractOne(each_interest, ab_interest_list)
            if score < 80:
                missing_in_ab_db.append(each_interest)
        except:
            missing_in_ab_db.append(each_interest)

    missing_in_almabase = re_interest_list + ab_interest_list
    missing_in_ab = list(process.dedupe(missing_in_almabase, threshold=80))
    print("Missing interests in Almabase: " + str(missing_in_ab))

    # Upload delta to AB
    if missing_in_ab_db != []:
        print("Uploading missing interests in Almabase")

        names = []
        for each_interest in missing_in_ab:
            name = {
                'name': each_interest
            }
            names.append(name)
        
        params = {
            'interests': names
        }
        url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
        patch_request_ab()
            
        # Will update in PostgreSQL
        for each_interest in missing_in_ab_db:
            insert_updates = """
                            INSERT INTO ab_interests_skills_added (ab_system_id, value, type, date)
                            VALUES (%s, %s, 'Interests', now())
                            """
            cur.execute(insert_updates, [ab_system_id, each_interest])
            conn.commit()
        print("Uploaded missing interests in Almabase")
        
    # Sync skills
    print("Syncing skills")
    # Get skills from RE
    print("Getting skills from RE")
    re_skill_list = []
    for each_value in re_api_response_custom_fields['value']:
        try:
            if each_value['category'] == "Skills":
                re_skill_list.append(each_value['value'])
        except:
            pass

    # Get interests from AB
    print("Getting skills from Almabase")
    url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=skills" % ab_system_id
    get_request_almabase()

    ab_skill_list = []
    for each_value in ab_api_response['skills']:
        try:
            ab_skill_list.append(each_value['name'])
        except:
            pass

    # Compare interests between RE & AB
    print("Comparing interests between RE & Almabase")
    missing_in_re = []
    for each_skill in ab_skill_list:
        try:
            likely_skill, score = process.extractOne(each_skill, re_skill_list)
            if score < 80:
                missing_in_re.append(each_skill)
        except:
            missing_in_re.append(each_skill)

    # Upload delta to RE
    if missing_in_re != []:
        print("Uploading delta to RE")

        for each_skill in missing_in_re:
            params = {
                'category': 'Skills',
                'value': each_skill,
                'comment': 'Added from AlmaBase',
                'date': datetime.now().replace(microsecond=0).isoformat(),
                'parent_id': re_system_id
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/constituents/customfields"
            post_request_re()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_interests_skills_added (re_system_id, value, type, date)
                            VALUES (%s, %s, 'Skills', now())
                            """
            cur.execute(insert_updates, [re_system_id, each_skill])
            conn.commit()

    # Compare interests between AB & RE
    print("Comparing interests between Almabase & RE")
    missing_in_ab_db = []
    for each_skill in re_skill_list:
        try:
            likely_skill, score = process.extractOne(each_skill, ab_skill_list)
            if score < 80:
                missing_in_ab_db.append(each_skill)
        except:
            missing_in_ab_db.append(each_skill)

    missing_in_almabase = re_skill_list + ab_skill_list
    missing_in_ab = list(process.dedupe(missing_in_almabase, threshold=80))  

    # Upload delta to AB
    if missing_in_ab_db != []:
        print("Uploading missing skills to Almabase")

        names = []
        for each_skill in missing_in_ab:
            name = {
                'name': each_skill
            }
            names.append(name)
        
        params = {
            'skills': names
        }
        url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
        patch_request_ab()
            
        # Will update in PostgreSQL
        for each_skill in missing_in_ab_db:
            insert_updates = """
                            INSERT INTO ab_interests_skills_added (ab_system_id, value, type, date)
                            VALUES (%s, %s, 'Skills', now())
                            """
            cur.execute(insert_updates, [ab_system_id, each_skill])
            conn.commit()
            print("Uploaded missing skills to Almabase")

    # Get Chapter from RE
    print("Getting Chapter from RE")
    re_chapter = ""
    try:
        for each_value in re_api_response_custom_fields['value']:
            if each_value['category'] == "Chapter":
                custom_field_id = each_value['id']
                re_chapter = each_value['value']
                break
    except:
        re_chapter = ""

    # Get Chapter from AlmaBase
    print("Getting Chapter from AlmaBase")
    try:
        ab_chapter = ab_profile['custom_fields']['chapter']['values'][0]['value']['content']
    except:
        ab_chapter = ""
        
    # Compare Chapters and update in RE
    print("Comparing Chapters and update in RE")
    if ab_chapter != "" and re_chapter != ab_chapter:
        
        if re_chapter == "":
            # Will post in RE
            print("Will add new chapter in RE")
            params = {
                'category': 'Chapter',
                'value': ab_chapter,
                'comment': 'Added from AlmaBase',
                'date': datetime.now().replace(microsecond=0).isoformat(),
                'parent_id': re_system_id
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/constituents/customfields"
            post_request_re()
            
        else:
            # Will patch in RE
            print("Will update chapter in RE")
            params = {
                'value': ab_chapter,
                'comment': 'Updated from AlmaBase',
                'date': datetime.now().replace(microsecond=0).isoformat(),
            }
            
            url = "https://api.sky.blackbaud.com/constituent/v1/constituents/customfields/%s" % custom_field_id
            patch_request_re()
        
        # Will update in PostgreSQL
        insert_updates = """
                        INSERT INTO re_interests_skills_added (re_system_id, value, type, date)
                        VALUES (%s, %s, 'Chapter', now())
                        """
        cur.execute(insert_updates, [re_system_id, ab_chapter])
        conn.commit()
        print("Updated Chapter in RE")
        
    # Life member update
    print("Checking if Alum is a Life Member")
    
    try:
        ab_life_member = ab_profile['custom_fields']['life_member']['values'][0]['value']['content']
    
    except:
        ab_life_member = 'no'

    if ab_life_member == "yes":
        print("Updating Life membership in RE")
        url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/constituentcodes" % re_system_id
        params = {}
        get_request_re()
        
        re_life_member = "no"
        try:
            for each_value in re_api_response['value']:
                if each_value['description'] == "Life Member":
                    re_life_member = "yes"
                    break
        except:
            re_life_member = "no"
        
        if re_life_member == "no":
            url = "https://api.sky.blackbaud.com/constituent/v1/constituentcodes"
            
            params = {
                'constituent_id': re_system_id,
                'description': 'Life Member'
            }
            
            post_request_re()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_interests_skills_added (re_system_id, value, type, date)
                            VALUES (%s, 'TRUE', 'Life Member', now())
                            """
            cur.execute(insert_updates, [re_system_id])
            conn.commit()
            print("Updated Life membership in RE")
            
    # Add RE ID in AlmaBase (external_database_id)
    print("Adding RE ID in AlmaBase as external_database_id")
    try:
        external_database_id = ab_profile['external_database_id']
    except:
        external_database_id = ""
        
    if external_database_id == "" or external_database_id is None or external_database_id == "Null" or external_database_id == "null":
        url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
        
        params = {
            'external_database_id': re_system_id
        }
        
        patch_request_ab()
        
        # Will update in PostgreSQL
        insert_updates = """
                        INSERT INTO ab_interests_skills_added (ab_system_id, value, type, date)
                        VALUES (%s, %s, 'External Database ID', now())
                        """
        cur.execute(insert_updates, [ab_system_id, re_system_id])
        conn.commit()
        print("Added RE ID in AlmaBase as external_database_id")
        
    # Add AlmaBase ID in Raisers Edge (Alias - Almabase ID)
    print("Adding AlmaBase ID in Raisers Edge as Alias - Almabase ID")
    try:
        url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/aliases" % re_system_id
        params = {}
        get_request_re()
        
        alias_id = ""
        for each_alias in re_api_response['value']:
            if each_alias['type'] == "Almabase ID":
                alias_id = each_alias['id']
                break
    except:
        alias_id = ""
        
    if alias_id == "":
        # Post Alias
        params = {
            'constituent_id': re_system_id,
            'name': ab_system_id,
            'type': "Almabase ID"
        }
        
        url = "https://api.sky.blackbaud.com/constituent/v1/aliases"
        post_request_re()
        
    else:
        # Patch Alias
        params = {
            'name': ab_system_id,
            'type': 'Almabase ID'
        }
        
        url = "https://api.sky.blackbaud.com/constituent/v1/aliases/%s" % alias_id
        patch_request_re()
        
    # Will update in PostgreSQL
    insert_updates = """
                    INSERT INTO already_synced (re_system_id, ab_system_id, date)
                    VALUES (%s, %s, now())
                    """
    cur.execute(insert_updates, [re_system_id, ab_system_id])
    conn.commit()
    print("Added RE ID in AlmaBase as external_database_id")
    
    # Close writing to Process.log
    if sys.stdout:
        sys.stdout.close()

except Exception as Argument:
    print("Error while syncing Alumni data between Raisers Edge & Almabase")
    subject = "Error while syncing Alumni data between Raisers Edge & Almabase"
    send_error_emails()
    
finally:
    
    # Close writing to Process.log
    if sys.stdout:
        sys.stdout.close()
    
    # Close DB connection
    if conn:
        cur.close()
        conn.close()
    
    sys.exit()