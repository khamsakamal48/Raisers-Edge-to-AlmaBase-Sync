import pandas as pd
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

# Retrieve access_token from file
with open('access_token_output.json') as access_token_output:
    data = json.load(access_token_output)
    access_token = data["access_token"]

# PostgreSQL DB Connection
conn = psycopg2.connect(host=DB_IP, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

# Open connection
cur = conn.cursor()

def get_request_re():
    # Request Headers for Blackbaud API request
    headers = {
        # Request headers
        'Bb-Api-Subscription-Key': RE_API_KEY,
        'Authorization': 'Bearer ' + access_token,
    }

    global re_api_response
    re_api_response = requests.get(url, params=params, headers=headers).json()

def delete_json_files():
    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            pass

# Housekeeping
fileList = glob.glob('Schools_in_RE_*.json')
delete_json_files()
fileList = glob.glob('Degrees_in_RE_*.json')
delete_json_files()

# Get School name list from RE
params = {}

# Table ID for School name in RE: 5010
url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/5010/tableentries?limit=5000"

# Pagination request to retreive list
while url:
    # Blackbaud API GET request
    get_request_re()

    # Incremental File name
    i = 1
    while os.path.exists("Schools_in_RE_%s.json" % i):
        i += 1
    with open("Schools_in_RE_%s.json" % i, "w") as list_output:
        json.dump(re_api_response, list_output,ensure_ascii=False, sort_keys=True, indent=4)

    # Check if a variable is present in file
    with open("Schools_in_RE_%s.json" % i) as list_output_last:
        if 'next_link' in list_output_last.read():
            url = re_api_response["next_link"]
        else:
            break

# Read multiple files
multiple_files = glob.glob("Schools_in_RE_*.json")

# Parse from JSON and write to CSV file
data = pd.DataFrame()

# Read each file
for each_file in multiple_files:

    # Open JSON file
    with open(each_file, 'r') as json_file:
        json_content = json.load(json_file)

        df = pd.json_normalize(json_content['value'])
        df = df[['table_entries_id', 'is_active', [], 'long_description', 'short_description', 'sequence', 'is_system_entry', 'code_tables_id', 'added_by_id', 'code_tables_name']]

        data = pd.concat([data, df])

data.to_csv('Schools_in_RE.csv', index=False, lineterminator='\r\n', sep=';')

# Delete paginated JSON files
# Get a list of all the file paths that ends with wildcard from in specified directory
fileList = glob.glob('Schools_in_RE_*.json')
delete_json_files()

# Delete rows in table
cur.execute("truncate re_schools;")

# Commit changes
conn.commit()

# Copying contents of CSV file to PostgreSQL DB
with open('Schools_in_RE.csv', 'r') as input_csv:
    # Skip the header row.
    next(input_csv)
    cur.copy_from(input_csv, 're_schools', sep=';')

# Commit changes
conn.commit()

# Table ID for Degree list in RE - 6
url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/6/tableentries?limit=5000"

# Pagination request to retreive list
while url:
    # Blackbaud API GET request
    get_request_re()

    # Incremental File name
    i = 1
    while os.path.exists("Degrees_in_RE_%s.json" % i):
        i += 1
    with open("Degrees_in_RE_%s.json" % i, "w") as list_output:
        json.dump(re_api_response, list_output,ensure_ascii=False, sort_keys=True, indent=4)

    # Check if a variable is present in file
    with open("Degrees_in_RE_%s.json" % i) as list_output_last:
        if 'next_link' in list_output_last.read():
            url = re_api_response["next_link"]
        else:
            break

# Read multiple files
multiple_files = glob.glob("Degrees_in_RE_*.json")

# Parse from JSON and write to CSV file
# Header of CSV file
header = ['table_entries_id', 'is_active', 'long_description', 'sequence', 'is_system_entry', 'code_tables_id', 'added_by_id', 'code_tables_name']

with open('Degrees_in_RE.csv', 'w', encoding='UTF8') as csv_file:
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
                data = (results['table_entries_id'],results['is_active'],results['long_description'].replace(";", ","),results['sequence'],results['is_system_entry'],results['code_tables_id'],results['added_by_id'],results['code_tables_name'])

                with open('Degrees_in_RE.csv', 'a', encoding='UTF8') as csv_file:
                    writer = csv.writer(csv_file, delimiter = ";")
                    writer.writerow(data)
            except:
                pass

# Delete paginated JSON files
# Get a list of all the file paths that ends with wildcard from in specified directory
fileList = glob.glob('Degrees_in_RE_*.json')
delete_json_files()

# Delete rows in table
cur.execute("truncate re_degrees;")

# Commit changes
conn.commit()

# Copying contents of CSV file to PostgreSQL DB
with open('Degrees_in_RE.csv', 'r') as input_csv:
    # Skip the header row.
    next(input_csv)
    cur.copy_from(input_csv, 're_degrees', sep=';')

# Commit changes
conn.commit()

# Table ID for Department list in RE - 1022
url = "https://api.sky.blackbaud.com/nxt-data-integration/v1/re/codetables/1022/tableentries?limit=5000"

# Pagination request to retreive list
while url:
    # Blackbaud API GET request
    get_request_re()

    # Incremental File name
    i = 1
    while os.path.exists("Departments_in_RE_%s.json" % i):
        i += 1
    with open("Departments_in_RE_%s.json" % i, "w") as list_output:
        json.dump(re_api_response, list_output,ensure_ascii=False, sort_keys=True, indent=4)

    # Check if a variable is present in file
    with open("Departments_in_RE_%s.json" % i) as list_output_last:
        if 'next_link' in list_output_last.read():
            url = re_api_response["next_link"]
        else:
            break

# Read multiple files
multiple_files = glob.glob("Departments_in_RE_*.json")

# Parse from JSON and write to CSV file
# Header of CSV file
header = ['table_entries_id', 'is_active', 'long_description', 'sequence', 'is_system_entry', 'code_tables_id', 'added_by_id', 'code_tables_name']

with open('Departments_in_RE.csv', 'w', encoding='UTF8') as csv_file:
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
                data = (results['table_entries_id'],results['is_active'],results['long_description'].replace(";", ","),results['sequence'],results['is_system_entry'],results['code_tables_id'],results['added_by_id'],results['code_tables_name'])

                with open('Departments_in_RE.csv', 'a', encoding='UTF8') as csv_file:
                    writer = csv.writer(csv_file, delimiter = ";")
                    writer.writerow(data)
            except:
                pass

# Delete paginated JSON files
# Get a list of all the file paths that ends with wildcard from in specified directory
fileList = glob.glob('Departments_in_RE_*.json')
delete_json_files()

# Delete rows in table
cur.execute("truncate re_departments;")

# Commit changes
conn.commit()

# Copying contents of CSV file to PostgreSQL DB
with open('Departments_in_RE.csv', 'r') as input_csv:
    # Skip the header row.
    next(input_csv)
    cur.copy_from(input_csv, 're_departments', sep=';')

# Commit changes
conn.commit()

# Close DB connection
cur.close()
conn.close()

# Delete CSV files
os.remove("Schools_in_RE.csv")
os.remove("Degrees_in_RE.csv")
os.remove("Departments_in_RE.csv")