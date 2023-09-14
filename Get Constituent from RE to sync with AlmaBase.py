import requests, os, json, glob, csv, psycopg2, sys, datetime, smtplib, ssl, imaplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from jinja2 import Environment
from datetime import datetime
import pandas as pd

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
RE_LIST_ID_1 = os.getenv("RE_LIST_ID_1")

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

    # Close writing to Process.log
    sys.stdout.close()

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
    message.attach(emailbody)
    attach_file_to_email(message, 'Process-Get_Constituent_from_RE_to_sync_with_AlmaBase.log')
    emailcontent = message.as_string()

    # # Create a secure SSL context
    # context = ssl.create_default_context()

    # # Try to log in to server and send email
    # try:
    #     server = smtplib.SMTP(SMTP_URL,SMTP_PORT)
    #     server.ehlo() # Can be omitted
    #     server.starttls(context=context) # Secure the connection
    #     server.ehlo() # Can be omitted
    #     server.login(MAIL_USERN, MAIL_PASSWORD)
    #     server.sendmail(MAIL_USERN, MAIL_USERN, emailcontent)
    #     # TODO: Send email here
    # except Exception as e:
    #     # Print any error messages to stdout
    #     print(e)
    # # finally:
    # #     server.quit()

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

# Printing the output to file for debugging
sys.stdout = open('Process-Get_Constituent_from_RE_to_sync_with_AlmaBase.log', 'w')

try:

    # Housekeeping
    fileList = glob.glob('Alums_in_RE_*.json')

    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            pass

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

    # List link - https://host.nxt.blackbaud.com/lists/shared-list/da749c96-9f38-4580-95e4-1d188f788d5e?envid=p-dzY8gGigKUidokeljxaQiA
    # Request parameters for Blackbaud API request
    params = {
        'list_id':RE_LIST_ID_1,
        'limit':'5000'
    }

    # Blackbaud API URL
    url = 'https://api.sky.blackbaud.com/constituent/v1/constituents'

    # Pagination request to retreive list
    while url:
        # Blackbaud API GET request
        get_request_re()

        # Incremental File name
        i = 1
        while os.path.exists("Alums_in_RE_%s.json" % i):
            i += 1
        with open("Alums_in_RE_%s.json" % i, "w") as list_output:
            json.dump(re_api_response, list_output,ensure_ascii=False, sort_keys=True, indent=4)

        # Check if a variable is present in file
        with open("Alums_in_RE_%s.json" % i) as list_output_last:
            if 'next_link' in list_output_last.read():
                url = re_api_response["next_link"]
            else:
                break

    # Read multiple files
    multiple_files = glob.glob("Alums_in_RE_*.json")

    # Parse from JSON and write to CSV file
    data = pd.DataFrame()

    # Read each file
    for each_file in multiple_files:

        # Open JSON file
        with open(each_file, 'r') as json_file:
            json_content = json.load(json_file)
            df = pd.json_normalize(json_content['value'])
            df = df[['id', 'name']]

            data = pd.concat([data, df])

    data.to_csv('Alums_in_RE.csv', index=False, lineterminator='\r\n', sep=';')

    # Delete paginated JSON files
    # Get a list of all the file paths that ends with wildcard from in specified directory
    fileList = glob.glob('Alums_in_RE_*.json')

    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            pass

    # PostgreSQL DB Connection
    conn = psycopg2.connect(host=DB_IP, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

    # Open connection
    cur = conn.cursor()

    # Delete rows in table
    cur.execute("truncate all_alums_in_re;")

    # Commit changes
    conn.commit()

    # Copying contents of CSV file to PostgreSQL DB
    with open('Alums_in_RE.csv', 'r') as input_csv:
        # Skip the header row.
        next(input_csv)
        cur.copy_from(input_csv, 'all_alums_in_re', sep=';')

    # Commit changes
    conn.commit()

    # Close writing to Process.log
    sys.stdout.close()

except Exception as Argument:

    print("Error while downloading Alumni data for syncing Alumni data between Raisers Edge & Almabase")
    subject = "Error while downloading Alumni data for syncing Alumni data between Raisers Edge & Almabase"

    send_error_emails()

finally:

    # Close DB connection
    if conn:
        cur.close()
        conn.close()

    sys.exit()