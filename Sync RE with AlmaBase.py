#!/usr/bin/env python3

import requests, os, json, glob, csv, psycopg2, sys, smtplib, ssl, imaplib, time, email, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment

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
    re_api_response = requests.patch(url, headers=headers, data=params)
    
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
        emails = (address['address'])
        ab_email_list.append(emails)
    except:
        pass

print(ab_email_list)

re_email_list = []
for address in re_api_response['value']:
    try:
        emails = (address['address'])
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

# Finding missing email addresses to be added in AlmaBase
set1 = set([i for i in re_email_list if i])
set2 = set(ab_email_list)

missing_in_ab = list(sorted(set1 - set2))
print(missing_in_ab)

print(ab_api_response)