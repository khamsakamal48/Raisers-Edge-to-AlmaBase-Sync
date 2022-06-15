#!/usr/bin/env python3

import requests, os, json, glob, csv, psycopg2

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
# Header of CSV file
header = ['System_ID', 'Name']

with open('Alums_in_RE.csv', 'w', encoding='UTF8') as csv_file:
    writer = csv.writer(csv_file, delimiter = ";")

    # Write the header
    writer.writerow(header)
    
# Read each file
for each_file in multiple_files:

    # Open JSON file
    with open(each_file, 'r') as json_file:
        json_content = json.load(json_file)

        for results in json_content['value']:
            try:
                data = (results['id'],results['name'])
                
                with open('Alums_in_RE.csv', 'a', encoding='UTF8') as csv_file:
                    writer = csv.writer(csv_file, delimiter = ";")
                    writer.writerow(data)
            except:
                pass
            
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

# Close DB connection
cur.close()
conn.close()