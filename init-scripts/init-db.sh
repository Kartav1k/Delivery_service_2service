#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE courier_service;
    CREATE DATABASE orders_delivery;
EOSQL
