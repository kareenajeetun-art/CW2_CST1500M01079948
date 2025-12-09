import pandas as pd
from app.data.db import connect_database

def insert_incident(date, incident_type, severity, status, description, reported_by=None):
    """Insert new incident."""
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cyber_incidents 
        (date, incident_type, severity, status, description, reported_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, incident_type, severity, status, description, reported_by))
    conn.commit()
    incident_id = cursor.lastrowid
    conn.close()
    return incident_id

def get_all_incidents():
    """Get all incidents as DataFrame."""
    conn = connect_database()
    df = pd.read_sql_query(
        "SELECT * FROM cyber_incidents ORDER BY id DESC",
        conn
    )
    conn.close()
    return df

def update_incident_status(conn, incident_id, new_status):
    """
    Update the status of an incident.
    """
    cursor = conn.cursor()

    # Update query
    query = """
        UPDATE cyber_incidents
        SET status = ?
        WHERE id = ?
    """

    cursor.execute(query, (new_status, incident_id))
    conn.commit()

    return cursor.rowcount

def delete_incident(conn, incident_id):
    """
    Delete an incident from the database.
    """
    cursor = conn.cursor()

    query = "DELETE FROM cyber_incidents WHERE id = ?"

    cursor.execute(query, (incident_id,))
    conn.commit()

    return cursor.rowcount

def get_incidents_by_type_count(conn):
    """
    Count incidents by type.
    Uses: SELECT, FROM, GROUP BY, ORDER BY
    """
    query = """
    SELECT incident_type, COUNT(*) as count
    FROM cyber_incidents
    GROUP BY incident_type
    ORDER BY count DESC
    """
    df = pd.read_sql_query(query, conn)
    return df

def get_high_severity_by_status(conn):
    """
    Count high severity incidents by status.
    Uses: SELECT, FROM, WHERE, GROUP BY, ORDER BY
    """
    query = """
    SELECT status, COUNT(*) as count
    FROM cyber_incidents
    WHERE severity = 'High'
    GROUP BY status
    ORDER BY count DESC
    """
    df = pd.read_sql_query(query, conn)
    return df

def get_incident_types_with_many_cases(conn, min_count=5):
    """
    Find incident types with more than min_count cases.
    Uses: SELECT, FROM, GROUP BY, HAVING, ORDER BY
    """
    query = """
    SELECT incident_type, COUNT(*) as count
    FROM cyber_incidents
    GROUP BY incident_type
    HAVING COUNT(*) > ?
    ORDER BY count DESC
    """
    df = pd.read_sql_query(query, conn, params=(min_count,))
    return df

def load_csv_to_table_incidents(conn, csv_path, table_name):

    # Check if CSV file exists
    if not csv_path.exists():
        print(f"⚠️  File not found: {csv_path}")
        print("   No incidents to migrate.")
        return
    
    # TODO: Read CSV using pandas.read_csv()
    #pd.read_csv(csv_path)
    df = pd.read_csv(csv_path)

    df = df.rename(columns={
        "timestamp": "date",
        "category": "incident_type"
    })

    # Add missing required columns with default values
    if "reported_by" not in df.columns:
        df["reported_by"] = "system"

    # Drop any extra columns not in the table definition (optional but cleaner)
    required_cols = ["date", "incident_type", "severity", "status", "description", "reported_by"]
    df = df[required_cols]

    # TODO: Use df.to_sql() to insert data
    # Parameters: name=table_name, con=conn, if_exists='append', index=False
    df.to_sql(
        name=table_name,
        con=conn,
        if_exists='append',
        index=False
    )
    
    # TODO: Print success message and return row count
    print(f"Loaded {len(df)} rows into '{table_name}'.")

    return len(df)
    #pass

