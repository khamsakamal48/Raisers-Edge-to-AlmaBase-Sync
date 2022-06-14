# Raisers-Edge-to-AlmaBase-Sync
sudo apt install python3-pip

pip3 install psycopg2
pip3 install python-dotenv
pip3 install fuzzywuzzy
pip3 install python-Levenshtein
pip3 install geopy

If you encounter error on installing pyscopg2, then try:

pip3 install psycopg2-binary

Install PostgreSQL

CREATE DATABASE "re-almabase-sync"

CREATE TABLE all_alums_in_re
(
    system_id character varying,
    name character varying
);

CREATE TABLE alread_synced
(
    system_id character varying,
    name character varying
);

CREATE TABLE re_emails_added
(
    system_id character varying,
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

Import Degree Mapping.csv to degree_mapping table
Import Department Mapping.csv to department_mapping table

Create a .env file with below parameters
DB_IP=
DB_NAME=
DB_USERNAME=
DB_PASSWORD=
AUTH_CODE=
REDIRECT_URL=
CLIENT_ID=
RE_API_KEY=
MAIL_USERN=
MAIL_PASSWORD=
IMAP_URL=
IMAP_PORT=
SMTP_URL=
SMTP_PORT=
SEND_TO=
ALMABASE_API_KEY=
ALMABASE_API_TOKEN=
RE_LIST_ID_1=