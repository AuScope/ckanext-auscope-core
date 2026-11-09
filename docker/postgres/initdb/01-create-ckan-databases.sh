#!/bin/bash
# Creates the CKAN role plus the development and test databases on first
# start of the PostgreSQL container (empty data volume only).
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set=ckan_db_user="$CKAN_DB_USER" \
    --set=ckan_db_password="$CKAN_DB_PASSWORD" <<-'EOSQL'
    CREATE ROLE :"ckan_db_user"
        WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
        PASSWORD :'ckan_db_password';
EOSQL

createdb --username "$POSTGRES_USER" --owner "$CKAN_DB_USER" --encoding UTF8 "$CKAN_DB"
createdb --username "$POSTGRES_USER" --owner "$CKAN_DB_USER" --encoding UTF8 "$CKAN_TEST_DB"
