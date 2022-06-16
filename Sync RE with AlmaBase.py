#!/usr/bin/env python3

from sqlite3 import paramstyle
from textwrap import indent
from click import echo
import requests, os, json, glob, csv, psycopg2, sys, smtplib, ssl, imaplib, time, email, re, fuzzywuzzy, itertools, geopy, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime

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

# PostgreSQL DB Connection
conn = psycopg2.connect(host=DB_IP, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

# Open connection
cur = conn.cursor()

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
    
    global re_api_response
    re_api_response = requests.get(url, params=params, headers=headers).json()
    
    check_for_errors()

def get_request_almabase():
    # Request Headers for AlmaBase API request
    headers = {
        "User-Agent":"Mozilla/5.0",
        'Accept': 'application/json',
        'X-API-Access-Key': ALMABASE_API_KEY,
        'X-API-Access-Token': ALMABASE_API_TOKEN,
    }
    
    global ab_api_response
    ab_api_response = requests.get(url, headers=headers).json()
    
    check_for_errors()
  
def post_request_re():
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json',
    }
    
    global re_api_response
    re_api_response = requests.post(url, params=params, headers=headers, json=params).json()
    
    check_for_errors()

def patch_request_re():
    headers = {
    # Request headers
    'Bb-Api-Subscription-Key': RE_API_KEY,
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
    }
    
    global re_api_response
    re_api_response = requests.patch(url, headers=headers, data=json.dumps(params))
    
    check_for_errors()
    
def patch_request_ab():
    # Request Headers for AlmaBase API request
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-Access-Key': ALMABASE_API_KEY,
        'X-API-Access-Token': ALMABASE_API_TOKEN,
    }
    
    global ab_api_response
    ab_api_response = requests.patch(url, headers=headers, json=params)
    
    check_for_errors()

def post_request_ab():
    # Request Headers for AlmaBase API request
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-Access-Key': ALMABASE_API_KEY,
        'X-API-Access-Token': ALMABASE_API_TOKEN,
    }
    
    global ab_api_response
    ab_api_response = requests.post(url, headers=headers, json=params)
    
    check_for_errors()
    
def check_for_errors():
    error_keywords = ["invalid", "error", "bad", "Unauthorized", "Forbidden", "Not Found", "Unsupported Media Type", "Too Many Requests", "Internal Server Error", "Service Unavailable", "Unexpected", "error_code", "400"]
    
    if any(x in re_api_response for x in error_keywords):
        # Send emails
        print ("Will send email now")
        send_error_emails()

def send_error_emails():
    print ("Calling function Send error emails")
    print (re_api_response)
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
    #     error_log_message=re_api_response,
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

def constituent_not_found_email():
    # Query the next data to uploaded in RE
    extract_sql = """
            SELECT name FROM all_alums_in_re EXCEPT SELECT name FROM alread_synced FETCH FIRST 1 ROW ONLY;
            """
    cur.execute(extract_sql)
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
            email_1=address,
        ), "html"
    )

    # Add HTML parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(emailbody)
    emailcontent = message.as_string()

    #   # Create secure connection with server and send email
    #   context = ssl._create_unverified_context()
    #   with smtplib.SMTP_SSL(SMTP_URL, SMTP_PORT, context=context) as server:
    #       server.login(MAIL_USERN, MAIL_PASSWORD)
    #       server.sendmail(
    #           MAIL_USERN, MAIL_USERN, emailcontent
    #       )

    # Create a secure SSL context
    context = ssl.create_default_context()
    
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(SMTP_URL,SMTP_PORT)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(MAIL_USERN, MAIL_PASSWORD)
        server.sendmail(MAIL_USERN, MAIL_USERN, emailcontent)
        # TODO: Send email here
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit() 

    # Save copy of the sent email to sent items folder
    with imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT) as imap:
        imap.login(MAIL_USERN, MAIL_PASSWORD)
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), emailcontent.encode('utf8'))
        imap.logout()

    # Close DB connection
    cur.close()
    conn.close()

    sys.exit()

def update_email_in_re():
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

# Query the next data to uploaded in RE
extract_sql = """
        SELECT system_id FROM all_alums_in_re EXCEPT SELECT system_id FROM alread_synced FETCH FIRST 1 ROW ONLY;
        """
cur.execute(extract_sql)
result = cur.fetchone()

# Ensure no comma or brackets in output
re_system_id = result[0]

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
    for address in re_api_response['value']:
        try:
            email = (address['address'])
            url = "https://api.almabaseapp.com/api/v1/profiles?search=%s&page=1&listed=true" % email
            get_request_almabase()
            count = ab_api_response["count"]
            if count == 1:
                break
        except:
            # Can't find Alum in AlmaBase
            status = ab_api_response["status"]
            if status == 404:
                subject = "Unable to find Alums in AlmaBase because of Network Failure"
            else:
                subject = "Unable to find Alums in AlmaBase for sync"
            constituent_not_found_email()
else:
    ab_system_id = ab_api_response["results"][0]["id"]

# Retrieve the AlmaBase Profile
url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id

get_request_almabase()

ab_profile = ab_api_response

# Get email list from AlmaBase
ab_email_list = []
for address in ab_profile['email_addresses']:
    try:
        emails = (address['address']).lower()
        ab_email_list.append(emails)
    except:
        pass

# Get list of available custom fields starting with email_id_
regex = re.compile('email_id_*')
email_id_list = [string for string in ab_profile['custom_fields'] if re.match(regex, string)]

blank_email_ids = []
for each_id in email_id_list:
    try:
        emails = (ab_profile['custom_fields'][each_id]['values'][0]['value']['content'])
        ab_email_list.append(emails)
    except:
        # Email IDs that don't have any email addresses in AlmaBase
        blank_email_ids.append(each_id)
        pass

re_email_list = []
for address in re_api_response['value']:
    try:
        emails = (address['address']).lower()
        re_email_list.append(emails)
    except:
        pass
    
# Finding missing email addresses to be added in RE
set1 = set([i for i in ab_email_list if i])
set2 = set(re_email_list)

missing_in_re = list(sorted(set1 - set2))

# Will update missing email IDs to RE
if missing_in_re != []:
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
            global new_email_type
            new_email_type = "Email " + str(incremental_max_count)
            update_email_in_re()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_emails_added (system_id, email, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [re_system_id, email_address])
            conn.commit()
        except:
            send_error_emails()

# Finding missing email addresses to be added in AlmaBase
set1 = set([i for i in re_email_list if i])
set2 = set(ab_email_list)

missing_in_ab = list(sorted(set1 - set2))

# Upload missing email addresses in AlmaBase
if missing_in_ab != []:
    for each_record in zip(missing_in_ab, blank_email_ids):
        try:
            each_email, each_id = each_record
            params = {
                'custom_fields': {
                    each_id: {
                        'type': 'email',
                        'label': each_id,      
                        'values': [
                            {
                                'value': {
                                    'content': each_email
                                    },
                                'display_order': int(each_id[-2:].replace("_", ""))
                                }
                            ]
                        }
                    }
                }
            url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
                
            patch_request_ab()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_emails_added (ab_system_id, email, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [ab_system_id, each_email])
            conn.commit()
        except:
            send_error_emails()
    
# Get list of of phone numbers in RE
url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/phones?include_inactive=true" % re_system_id
get_request_re()

re_phone_list = []
for each_phone in re_api_response['value']:
    try:
        phones = re.sub("[^0-9]", "",(each_phone['number']))
        re_phone_list.append(phones)
    except:
        pass
    
# Get list of phone numbers in AlmaBase
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
regex = re.compile('\w+phone|\w+fax|\w+mobile|\w+pager')
phone_id_list = [string for string in ab_profile['custom_fields'] if re.match(regex, string)]

blank_phone_ids = []
for each_id in phone_id_list:
    try:
        phones = re.sub("[^0-9]", "",(ab_profile['custom_fields'][each_id]['values'][0]['value']['content']))
        ab_phone_list.append(phones)
    except:
        # Email IDs that don't have any email addresses in AlmaBase
        blank_phone_ids.append(each_id)
        pass

# Finding missing phone numbers to be added in RE
missing_in_re = []
for each_phone in ab_phone_list:
    try:
        likely_phone, score = process.extractOne(each_phone, re_phone_list)
        if score < 80:
            missing_in_re.append(each_phone)
    except:
        missing_in_re.append(each_phone)

# Making sure that there are no duplicates in the missing list
if missing_in_re != []:
    missing = list(process.dedupe(missing_in_re, threshold=80))
    missing_in_re = missing

# Upload missing numbers in RE
if missing_in_re != []:
    for each_phone in missing_in_re:
        try:
            url = "https://api.sky.blackbaud.com/constituent/v1/phones"
        
            params = {
                'constituent_id': re_system_id,
                'number': each_phone,
                'type': 'Mobile'
            }
            
            post_request_re()
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_phone_added (re_system_id, phone, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [re_system_id, each_phone])
            conn.commit()
        except:
            pass
        
# Finding missing phone numbers to be added in AlmaBase
missing_in_ab = []
for each_phone in re_phone_list:
    try:
        likely_phone, score = process.extractOne(each_phone, ab_phone_list)
        if score < 80:
            missing_in_ab.append(each_phone)
    except:
        missing_in_ab.append(each_phone)

# Making sure that there are no duplicates in the missing list
if missing_in_ab != []:
    missing = list(process.dedupe(missing_in_ab, threshold=80))
    missing_in_ab = missing

# Upload missing numbers in AlmaBase
if missing_in_ab != []:
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
        except:
            send_error_emails()
            
# Get Relation list from RE
url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/relationships" % re_system_id
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
url = "https://api.almabaseapp.com/api/v1/profiles/%s/employments" % ab_system_id
get_request_almabase()

ab_api_response_org = ab_api_response
ab_org_name_list = []

for each_org in ab_api_response['results']:
    try:
        # Retrieve the org name
        ab_org_name_list.append(each_org['employer']['name'])
    except:
        pass

# Finding missing employments to be added in RE
missing_in_re = []
for each_org in ab_org_name_list:
    try:
        likely_phone, score = process.extractOne(each_org, re_org_name_list)
        if score < 90:
            missing_in_re.append(each_org)
    except:
        missing_in_re.append(each_org)

# Making sure that there are no duplicates in the missing list
if missing_in_re != []:
    missing = list(process.dedupe(missing_in_re, threshold=80))
    missing_in_re = missing

# Upload missing employments in RE
if missing_in_re != []:
    for each_org in missing_in_re:
        try:
            for each_ab_org in ab_api_response_org['results']:
                if each_org == each_ab_org['employer']['name']:
                    position = each_ab_org['designation']['name']
                    if position is None:
                        position = ""
                    start_month = each_ab_org['start_month']
                    if start_month is None:
                        start_month = ""
                    start_year = each_ab_org['start_year']
                    if start_year is None:
                        start_year = ""
                    end_month = each_ab_org['end_month']
                    if end_month is None:
                        end_month = ""
                    end_year = each_ab_org['end_year']
                    if end_year is None:
                        end_year = ""
                    break
        except:
            pass
        
        # Check if organisation is a University
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
        print(params)
        
        url = "https://api.sky.blackbaud.com/constituent/v1/relationships"
        
        post_request_re()
     
# Update missing details in RE
for each_org in re_api_response_org['value']:
    try:
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
                    if re_org_position != "" or ab_org_position == "":
                        ab_org_position = ""
                        
                    # Check if joining year needs an update
                    if re_org_start_year != "" or ab_org_start_year == "":
                        ab_org_start_month = ""
                        ab_org_start_year = ""
                        
                    # Check if leaving year needs an update
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
    except:
        pass
      
# Finding missing employments to be added in AlmaBase
missing_in_ab = []
for each_org in re_org_name_list:
    try:
        likely_phone, score = process.extractOne(each_org, ab_org_name_list)
        if score < 90:
            missing_in_ab.append(each_org)
    except:
        missing_in_ab.append(each_org)
    
# Making sure that there are no duplicates in the missing list
if missing_in_ab != []:
    missing = list(process.dedupe(missing_in_ab, threshold=80))
    missing_in_ab = missing

# Upload missing employments in RE
if missing_in_ab != []:
    for each_org in missing_in_ab:
        try:
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
                        # Create an employment in RE
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
                    break
        except:
            pass

# Update missing details in AlmaBase
for each_org in ab_api_response_org['results']:
    try:
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
                    if re_org_position == "" or ab_org_position != "":
                        re_org_position = ""
                        
                    # Check if joining year needs an update
                    if re_org_start_year == "" or ab_org_start_year != "":
                        re_org_start_month = ""
                        re_org_start_year = ""
                        
                    # Check if leaving year needs an update
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
    except:
        pass
    
# Retrieve addresses from RE
url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/addresses?include_inactive=true" % re_system_id
get_request_re()

re_api_response_address = re_api_response

# Retrieve addresses from Almabase - 1
url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=addresses" % ab_system_id

get_request_almabase()
ab_api_response_address = ab_api_response

# Retrieve addresses from Almabase - 2
url = "https://api.almabaseapp.com/api/v1/profiles/%s?fields=custom_fields" % ab_system_id

get_request_almabase()
ab_api_response_address_custom_fields = ab_api_response

# Retrive details from Permanent address in AlmaBase
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

# Retrive details from Work address in AlmaBase
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
    ab_api_response_address['addresses'].append(each_address)

# Compare the ones in RE with AB and find delta
re_address_list = []
for each_value in re_api_response_address['value']:
    re_address = each_value['formatted_address'].replace("\r\n",", ")
    re_address_list.append(re_address)

# Finding missing addresses to be added in RE
missing_in_re = []
for each_value in ab_api_response_address['addresses']:
    try:
        try:
            line1 = each_value['line1']
            if line1 is None:
                line1 = ""
        except:
            line1 = ""
            
        try:
            line2 = each_value['line2']
            if line2 is None:
                line2 = ""
        except:
            line2 = ""
        
        try:
            city = each_value['location']['city']
            if city is None:
                city = ""
        except:
            city = ""
        
        try:
            state = each_value['location']['state']
            if state is None:
                state = ""
        except:
            try:
                state = each_value['location']['county']
                if state is None:
                    state = ""
            except:
                state = ""
                
        try:
            country = each_value['location']['country']
            if country is None:
                country = ""
        except:
            country = ""
            
        try:
            zip_code = each_value['zip_code']
            if zip_code is None:
                zip_code = ""
        except:
            zip_code = ""
        
        if  line1 != "" or line2 != "" or city != "" or state != "" or country != "" or zip_code != "":
            ab_address = line1 + " " + line2 + " " + city + " " + state + " " + country + " " + zip_code
            
            try:
                likely_address, score = process.extractOne(ab_address, re_address_list)
                if score < 80:
                    missing_in_re.append(ab_address)
            except:
                missing_in_re.append(ab_address)
    except:
        pass

# Making sure that there are no duplicates in the missing list
if missing_in_re != []:
    missing = list(process.dedupe(missing_in_re, threshold=80))
    missing_in_re = missing

# Create missing address in RE
if missing_in_re != []:
    for address in missing_in_re:
        try:
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
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO re_address_added (re_system_id, address, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [re_system_id, address])
            conn.commit()
        except:
            pass

# Compare the ones in AB with RE and find delta
ab_address_list = []
for each_value in ab_api_response_address['addresses']:
    try:
        line1 = each_value['line1']
        if line1 is None:
            line1 = ""
    except:
        line1 = ""
        
    try:
        line2 = each_value['line2']
        if line2 is None:
            line2 = ""
    except:
        line2 = ""
    
    try:
        city = each_value['location']['city']
        if city is None:
            city = ""
    except:
        city = ""
    
    try:
        state = each_value['location']['state']
        if state is None:
            state = ""
    except:
        try:
            state = each_value['location']['county']
            if state is None:
                state = ""
        except:
            state = ""
            
    try:
        country = each_value['location']['country']
        if country is None:
            country = ""
    except:
        country = ""
        
    try:
        zip_code = each_value['zip_code']
        if zip_code is None:
            zip_code = ""
    except:
        zip_code = ""
        
    ab_address = (line1 + " " + line2 + " " + city + " " + state + " " + country + " " + zip_code).replace("  ", " ")
    ab_address_list.append(ab_address)

# Finding missing addresses to be added in AlmaBase
missing_in_ab = []
for each_value in re_api_response_address['value']:
    re_address = each_value['formatted_address'].replace("\r\n",", ")
    
    try:
        likely_address, score = process.extractOne(re_address, ab_address_list)
        if score < 80:
            missing_in_ab.append(re_address)
    except:
        missing_in_ab.append(re_address)

# Making sure that there are no duplicates in the missing list
if missing_in_ab != []:
    missing = list(process.dedupe(missing_in_ab, threshold=80))
    missing_in_ab = missing

# Create missing address in AB
if missing_in_ab != []:
    i = 0
    for address in missing_in_ab:
        try:
            # Check where the new address can be added
            while i == 0:
                for each_value in ab_api_response_address['addresses']:
                    try:
                        line1 = each_value['line1']
                        if line1 is None:
                            line1 = ""
                    except:
                        line1 = ""
                        
                    try:
                        line2 = each_value['line2']
                        if line2 is None:
                            line2 = ""
                    except:
                        line2 = ""
                    
                    try:
                        city = each_value['location']['city']
                        if city is None:
                            city = ""
                    except:
                        city = ""
                    
                    try:
                        state = each_value['location']['state']
                        if state is None:
                            state = ""
                    except:
                        try:
                            state = each_value['location']['county']
                            if state is None:
                                state = ""
                        except:
                            state = ""
                            
                    try:
                        country = each_value['location']['country']
                        if country is None:
                            country = ""
                    except:
                        country = ""
                        
                    try:
                        zip_code = each_value['zip_code']
                        if zip_code is None:
                            zip_code = ""
                    except:
                        zip_code = ""
                    
                    if line1 != "" or line2 != "" or city != "" or state != "" or country != country or zip_code != "":
                        i += 1
                        
                        # Stop after 4 addresses
                        if i == 4:
                            break
                else:
                    break
            
            ab_address_number = i + 1
            
            # Get city, state and country from Address
            get_address(address)
            
            # Patch Profile
            url = "https://api.almabaseapp.com/api/v1/profiles/%s" % ab_system_id
            
            # Will add as address    
            if ab_address_number <= 2:
                
                params = {
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
            
            # Will add as custom field - permanent address   
            elif ab_address_number == 3:
                
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
            
            else:
                
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
            
            patch_request_ab()
            i += 1
            
            # Will update in PostgreSQL
            insert_updates = """
                            INSERT INTO ab_address_added (ab_system_id, address, date)
                            VALUES (%s, %s, now())
                            """
            cur.execute(insert_updates, [ab_system_id, address])
            conn.commit()
        except:
            pass
        
# Retrieve IITB education from RE
url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s/educations" % re_system_id

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
url = "https://api.almabaseapp.com/api/v1/profiles/%s/educations" % ab_system_id

get_request_almabase()
ab_api_response_education = ab_api_response

# Compare the ones present in RE with AlmaBase and find delta
# When only one education exists in both
if len(re_api_response_education['value']) == 1 and ab_api_response_education['count'] == 1:
    
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
    try:
        ab_class_of = ab_api_response_education['results'][0]['class_year']
        
        if int(ab_class_of) < 1962 or ab_class_of == "null" or ab_class_of is None:
            ab_class_of = ""
    except:
        ab_class_of = ""
        
    try:
        ab_department = ab_api_response_education['results'][0]['course']['name']
        
        if ab_department == "null" or ab_department is None:
            ab_department = ""
    except:
        ab_department = ""
        
    try:
        ab_department = ab_api_response_education['results'][0]['branch']['name']
        
        if ab_department == "null" or ab_department is None:
            ab_department = ""
    except:
        ab_department = ""
        
    try:
        ab_degree = ab_api_response_education['results'][0]['course']['name']
        
        if ab_degree == "null" or ab_degree is None:
            ab_degree = ""
    except:
        ab_degree = ""
        
    try:
        ab_hostel = ab_api_response_education['results'][0]['custom_fields']['hostel']['values'][0]['value']['label']
        
        if ab_hostel == "null" or ab_hostel is None:
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
            
        if params != {}:
            url = "https://api.sky.blackbaud.com/constituent/v1/educations/%s" % re_education_id
            patch_request_re()
            
        # Will update in PostgreSQL
        insert_updates = """
                        INSERT INTO re_iitb_education_added (re_system_id, roll_number, department, joining_year, class_of, degree, hostel, date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                        """
        cur.execute(insert_updates, [re_system_id, re_roll_number, re_department, re_joining_year, re_class_of, re_degree, re_hostel])
        conn.commit()
    
    # # Compare the ones present in AlmaBase with RE and find delta
    # if ab_class_of == "" or ab_department == "" or ab_degree == "" or ab_hostel == "" or ab_joining_year == "" or ab_roll_number == "":
    #     if re_class_of != "" and ab_class_of == "":
    #         ab_class_of = re_class_of
            
    #     if re_department != "" and ab_department == "":
    #         extract_department = """
    #         SELECT ab_department FROM department_mapping WHERE re_department = '%s' FETCH FIRST 1 ROW ONLY;
    #         """
    #         cur.execute(extract_sql, [re_department])
    #         result = cur.fetchone()
            
    #         # Ensure no comma or brackets in output
    #         ab_department = result[0]
            
    #     if re_degree != "" and ab_degree == "":
    #         extract_degree = """
    #         SELECT ab_degree FROM degree_mapping WHERE re_degree = '%s' FETCH FIRST 1 ROW ONLY;
    #         """
    #         cur.execute(extract_degree, [re_degree])
    #         result = cur.fetchone()
            
    #         # Ensure no comma or brackets in output
    #         ab_degree = result[0]
            
    #     if re_hostel != "" and ab_hostel == "":
    #         # Taking the last Hostel after comma
    #         ab_hostel = re_hostel[re_hostel.rfind(",") +1:].lower().replace(" ","_")
    #     else:
    #         ab_hostel_content = ab_hostel.lower().replace(" ","_")
    #         ab_hostel = ab_hostel_content
            
    #     if re_joining_year != "" and ab_joining_year == "":
    #         ab_joining_year = re_joining_year
            
    #     if re_roll_number != "" and ab_roll_number == "":
    #             ab_roll_number = re_roll_number
            
    #     params_ab = {
    #         'course': {
    #             'name': ab_degree
    #             },
    #         'branch': {
    #             'name': ab_department
    #             },
    #         'custom_fields': {
    #             'hostel': {
    #                 'values': [
    #                     {
    #                         'value': {
    #                             'content': ab_hostel
    #                         },
    #                         'display_order': 0
    #                     }
    #                 ]
    #             }
    #         },
    #         'year_of_graduation': ab_class_of,
    #         'year_of_joining': ab_joining_year,
    #         'year_of_leaving': ab_class_of,
    #         'roll_number': ab_roll_number,
    #         'college': {
    #             'name': "IIT Bombay"
    #         }
    #     }
        
    #     # Delete blank values from JSON
    #     for i in range(10):
    #         params = del_blank_values_in_json(params_ab.copy())
            
    #     print_json(params)
        
    #     if params != {} and ab_class_of != "":
    #         url = "https://api.almabaseapp.com/api/profiles/%s/educations" % (ab_system_id, ab_education_id)
    #         print(url)
    #         patch_request_ab()
    #         print(ab_api_response)
    
# When more than one exists
else:
    subject = "Multiple IITB Education details exists in either Raisers Edge or AlmaBase for syncing"
    constituent_not_found_email()

# Get other education details from RE
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
missing_in_re = []
for each_school in ab_other_school_name_list:
    try:
        likely_school, score = process.extractOne(each_school, re_other_school_name_list)
        if score < 80:
            missing_in_re.append(each_school)
    except:
        missing_in_re.append(each_school)
        
# Add missing records in RE
if missing_in_re != []:
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
                
                # Will update in PostgreSQL
                insert_updates = """
                                INSERT INTO re_other_education_added (re_system_id, school_name, date)
                                VALUES (%s, %s, now())
                                """
                cur.execute(insert_updates, [re_system_id, likely_school])
                conn.commit()
            else:
                # Will add a new school in RE
                try:
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
                    
                    # Will update in PostgreSQL
                    insert_updates = """
                                    INSERT INTO re_other_education_added (re_system_id, school_name, date)
                                    VALUES (%s, %s, now())
                                    """
                    cur.execute(insert_updates, [re_system_id, likely_school])
                    conn.commit()
                except:
                    pass
        except:
            pass

# Finding missing other schools to be added in AlmaBase
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
        try:
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
        except:
            pass

# Sync Generic person Details
# Get personal details from RE
url = "https://api.sky.blackbaud.com/constituent/v1/constituents/%s" % re_system_id
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
    
re_dob = re_dob_year + "-" + re_dob_month + "-" + re_dob_day

try:
    re_first_name = re_api_response_generic_details['first']
    if re_first_name is None or re_first_name =="Null" or re_first_name == "null":
        re_first_name = ""
except:
    re_first_name = ""
    
try:
    re_last_name = re_api_response_generic_details['last']
    if re_last_name is None or re_last_name =="Null" or re_last_name == "null":
        re_last_name = ""
except:
    re_last_name = ""

try:
    re_deceased = re_api_response_generic_details['deceased']
    if re_deceased is None or re_deceased =="Null" or re_deceased == "null":
        re_deceased = ""
except:
    re_deceased = ""

# Get personal details from Almabase
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
except:
    ab_dob = ""

try:
    ab_first_name = ab_api_response_generic_details['first_name']
    if ab_first_name is None or ab_first_name =="Null" or ab_first_name == "null":
        ab_first_name = ""
except:
    ab_first_name = ""
    
try:
    ab_last_name = ab_api_response_generic_details['last_name']
    if ab_last_name is None or ab_last_name =="Null" or ab_last_name == "null":
        ab_last_name = ""
except:
    ab_last_name = ""

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
if re_gender == "" and ab_gender != "":
    re_gender_update = ab_gender
# elif re_gender == "" and ab_gender == "":
    

if len(re_dob) < len(ab_dob):
    re_dob_update = ab_dob
else:
    re_dob_update = ""




# Find delta and upload
# Compare AB with RE
# Find delta and upload
