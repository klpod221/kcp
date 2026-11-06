#!/bin/bash
set -e

# Creates application-specific databases if they do not already exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE mcp_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp_db')\gexec
EOSQL

