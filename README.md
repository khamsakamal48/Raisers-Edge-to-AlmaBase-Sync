# Raisers-Edge-to-AlmaBase-Sync
sudo apt install python3-pip

pip3 install psycopg2
pip3 install python-dotenv

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