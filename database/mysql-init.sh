#!/bin/bash
set -e

# Wait for MySQL to start
echo "Waiting for MySQL to start..."
sleep 10

# Check if database is already initialized
if [ ! -d "/var/lib/mysql/${MYSQL_DATABASE}" ]; then
    echo "Database not found. Initializing..."
    mysql -uroot -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/init.sql
    mysql -uroot -p"$MYSQL_ROOT_PASSWORD" < /docker-entrypoint-initdb.d/feed_database.sql
    echo "Database initialized successfully."
else
    echo "Database already exists. Skipping initialization."
fi

# Run MySQL in foreground
exec docker-entrypoint.sh mysqld