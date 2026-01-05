PGUSER=postgres
SQL_FILE=sql/init_db.sql

echo "Running database setup..."
psql -U $PGUSER -f $SQL_FILE

echo "Database setup complete."