# Raisers Edge to AlmaBase Sync

Raisers Edge to AlmaBase Sync is a program written in Python to compare IIT Bombay's Alumni data between Raiser's Edge and Almabase and update the missing data in the respective databases.

## Pre-requisites / Installation
- Install **Python3** and python modules using pip3
```bash

# To install python3 and pip3
sudo apt install python3-pip

# Python Modules
pip3 install psycopg2
pip3 install python-dotenv
pip3 install fuzzywuzzy
pip3 install python-Levenshtein
pip3 install geopy

```
- If you encounter error on installing **pyscopg2**, then try:
```bash

pip3 install psycopg2-binary

```

- Install **PostgreSQL** using the steps mentioned [here](https://www.postgresql.org/download/linux/ubuntu/).
```bash

sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt -y install postgresql

```

- Create required **Databases**
```sql

CREATE DATABASE "re-almabase-sync"

CREATE TABLE all_alums_in_re
(
    re_system_id character varying,
    name character varying
);

CREATE TABLE already_synced
(
    re_system_id character varying,
    ab_system_id character varying,
    date date
);

CREATE TABLE re_emails_added
(
    re_system_id character varying,
    email character varying,
    date date
);

CREATE TABLE ab_emails_added
(
    ab_system_id character varying,
    email character varying,
    date date
);

CREATE TABLE re_phone_added
(
    re_system_id character varying,
    phone character varying,
    date date
);

CREATE TABLE ab_phone_added
(
    ab_system_id character varying,
    phone character varying,
    date date
);

CREATE TABLE re_address_added
(
    re_system_id character varying,
    address character varying,
    date date
);

CREATE TABLE ab_address_added
(
    ab_system_id character varying,
    address character varying,
    date date
);

CREATE TABLE degree_mapping
(
    ab_degree character varying,
    re_degree character varying
);

CREATE TABLE department_mapping
(
    ab_department character varying,
    re_department character varying
);

CREATE TABLE re_iitb_education_added
(
    re_system_id character varying,
    roll_number character varying,
    department character varying,
    joining_year character varying,
    class_of character varying,
    degree character varying,
    hostel character varying,
    date date
);

CREATE TABLE re_schools
(
    table_entries_id character varying,
    is_active character varying,
    long_description character varying,
    short_description character varying,
    sequence character varying,
    is_system_entry character varying,
    code_tables_id character varying,
    added_by_id character varying,
    code_tables_name character varying
);

CREATE TABLE re_degrees
(
    table_entries_id character varying,
    is_active character varying,
    long_description character varying,
    sequence character varying,
    is_system_entry character varying,
    code_tables_id character varying,
    added_by_id character varying,
    code_tables_name character varying
);

CREATE TABLE re_departments
(
    table_entries_id character varying,
    is_active character varying,
    long_description character varying,
    sequence character varying,
    is_system_entry character varying,
    code_tables_id character varying,
    added_by_id character varying,
    code_tables_name character varying
);

CREATE TABLE re_other_education_added
(
    re_system_id character varying,
    school_name character varying,
    date date
);

CREATE TABLE ab_other_education_added
(
    ab_system_id character varying,
    school_name character varying,
    date date
);

CREATE TABLE re_personal_details_added
(
    re_system_id character varying,
    birth_day character varying,
    birth_month character varying,
    deceased character varying,
    first_name character varying,
    former_name character varying,
    gender character varying,
    last_name character varying,
    middle_name character varying,
    preferred_name character varying,
    date date
);

CREATE TABLE ab_personal_details_added
(
    ab_system_id character varying,
    first_name character varying,
    middle_name character varying,
    last_name character varying,
    gender character varying,
    dob character varying,
    deceased character varying,
    date date
);

CREATE TABLE re_social_media_added
(
    re_system_id character varying,
    address character varying,
    type character varying,
    date date
);

CREATE TABLE ab_social_media_added
(
    ab_system_id character varying,
    address character varying,
    type character varying,
    date date
);

CREATE TABLE re_interests_skills_added
(
    re_system_id character varying,
    value character varying,
    type character varying,
    date date
);

CREATE TABLE ab_interests_skills_added
(
    ab_system_id character varying,
    value character varying,
    type character varying,
    date date
);

```

- Import **Degree Mapping.csv** to ***degree_mapping*** table
- Import **Department Mapping.csv** to ***department_mapping*** table
- Create a **.env** file with below parameters. ***`Replace # ... with appropriate values`***

```bash

DB_IP=# IP of SQL Database
DB_NAME=# Name of SQL Database
DB_USERNAME=# Login for SQL Database
DB_PASSWORD=# Password for SQL Database
AUTH_CODE= # Raiser's Edge NXT Auth Code (encode Client 
REDIRECT_URL=# Redirect URL of application in Raiser's Edge NXT
CLIENT_ID=# Client ID of application in Raiser's Edge NXT
RE_API_KEY=# Raiser's Edge NXT Developer API Key
MAIL_USERN= # Email Username
MAIL_PASSWORD= # Email password
IMAP_URL=# IMAP web address
IMAP_PORT=# IMAP Port
SMTP_URL=# SMTP web address
SMTP_PORT=# SMTP Port
SEND_TO=# Email ID of user who needs to receive error emails (if any)
ALMABASE_API_KEY=# AlmaBase Developer API Key
ALMABASE_API_TOKEN=# AlmaBase Developer API Token
RE_LIST_ID_1=# ID of list in Raiser's Edge NXT that'll give the list of all Alums

```

## Usage
```bash

python3 Request Access Token.py

```
- Copy and paste the link in a browser to get the **TOKEN**
- Copy the **TOKEN** in the terminal and press ENTER
- Set a CRON job to refresh token and start the program
```bash

crontab -e

```
- Set below CRON jobs
```bash

*/42 * * * * cd Raisers-Edge-to-AlmaBase-Sync/ && python3 Refresh\ Access\ Token.py > /dev/null 2>&1
@monthly cd Raisers-Edge-to-AlmaBase-Sync/ && python3 Get\ Constituent\ from\ RE\ to\ sync\ with\ AlmaBase.py > /dev/null 2>&1
@weekly cd Raisers-Edge-to-AlmaBase-Sync/ && python3 Get\ Education\ Details\ from\ RE.py > /dev/null 2>&1
*/10 * * * * cd Raisers-Edge-to-AlmaBase-Sync/ && python3 Sync\ RE\ with\ AlmaBase.py > /dev/null 2>&1

```
- Monitor emails for any errors and take appropriate action.