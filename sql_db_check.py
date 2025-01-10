import psycopg2  
  
# Database connection details  
SQL_SERVER_NAME = 'localhost'  
SQL_SERVER_PORT = '5432'  
SQL_SERVER_DATABASE = 'dailypulse'  
SQL_SERVER_USERNAME = 'postgres'  
SQL_SERVER_PASSWORD = 'admin'  
  
# Connection string  
conn_str = f"dbname='{SQL_SERVER_DATABASE}' user='{SQL_SERVER_USERNAME}' host='{SQL_SERVER_NAME}' port='{SQL_SERVER_PORT}' password='{SQL_SERVER_PASSWORD}'"  
  
# Connect to the database  
try:  
    conn = psycopg2.connect(conn_str)  
    print("Connection successful")  
  
    cursor = conn.cursor()  
  
    # Execute the query to list all tables  
    cursor.execute("""  
    SELECT table_schema, table_name  
    FROM information_schema.tables  
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')  
    AND table_type = 'BASE TABLE'  
    ORDER BY table_schema, table_name;  
    """)  
  
    # Fetch all rows from the executed query  
    tables = cursor.fetchall()  
  
    # Print the fetched tables  
    print("List of tables:")  
    for table in tables:  
        print(f"Schema: {table[0]}, Table: {table[1]}")  
  
    # Close the cursor and connection  
    cursor.close()  
    conn.close()  
  
except psycopg2.Error as e:  
    print("Error in connection:", e)  