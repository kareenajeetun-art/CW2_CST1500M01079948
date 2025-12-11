import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from app.data.db import connect_database



def insert_it_ticket(ticket_id, priority, status, category, subject,
                     description=None, created_date=None,
                     resolved_date=None, assigned_to=None):
    """Insert a new IT ticket record."""
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO it_tickets
        (ticket_id, priority, status, category, subject,
         description, created_date, resolved_date, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticket_id, priority, status, category, subject,
          description, created_date, resolved_date, assigned_to))

    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id




def get_all_it_tickets():
    """Return all IT tickets as a DataFrame."""
    conn = connect_database()
    df = pd.read_sql_query("SELECT * FROM it_tickets ORDER BY id DESC", conn)
    conn.close()
    return df




def update_it_ticket(conn, ticket_id, field, new_value):
    """Update a specific field of an IT ticket."""
    cursor = conn.cursor()
    query = f"UPDATE it_tickets SET {field} = ? WHERE id = ?"
    cursor.execute(query, (new_value, ticket_id))
    conn.commit()
    return cursor.rowcount




def delete_it_ticket(conn, ticket_id):
    """Delete an IT ticket by ID."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM it_tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    return cursor.rowcount




def count_tickets_by_priority(conn):
    """Count tickets grouped by priority."""
    query = """
    SELECT priority, COUNT(*) AS count
    FROM it_tickets
    GROUP BY priority
    ORDER BY count DESC
    """
    return pd.read_sql_query(query, conn)


def count_tickets_by_status(conn):
    """Count tickets grouped by status."""
    query = """
    SELECT status, COUNT(*) AS count
    FROM it_tickets
    GROUP BY status
    ORDER BY count DESC
    """
    return pd.read_sql_query(query, conn)


def unresolved_tickets(conn):
    """Return all tickets not resolved."""
    query = """
    SELECT * FROM it_tickets
    WHERE status != 'Resolved'
    ORDER BY created_date DESC
    """
    return pd.read_sql_query(query, conn)


def average_resolution_time(conn):
    """Compute average resolution hours for resolved tickets."""
    query = """
    SELECT AVG(
        JULIANDAY(resolved_date) - JULIANDAY(created_date)
    ) * 24 AS avg_resolution_hours
    FROM it_tickets
    WHERE resolved_date IS NOT NULL
    """
    return pd.read_sql_query(query, conn)




def load_csv_to_table_it_tickets(conn, csv_path, table_name):
    """Load IT tickets CSV into the database."""

    csv_path = Path(csv_path)

    if not csv_path.exists():
        print(f"⚠️ File not found: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)

    # Rename columns into DB format
    df = df.rename(columns={
        "created_at": "created_date"
    })

    # Add category (CSV doesn't include it)
    df["category"] = "General"

    # Build subject (first two words of description)
    df["subject"] = df["description"].apply(lambda d: " ".join(d.split()[:2]) if isinstance(d, str) else "No Subject")

    # Compute resolved_date
    resolved_dates = []
    for _, row in df.iterrows():
        created = row["created_date"]
        hours = row["resolution_time_hours"]
        status = row["status"]

        if status != "Resolved":
            resolved_dates.append(None)
        else:
            ts = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
            resolved_dates.append(ts + timedelta(hours=int(hours)))

    df["resolved_date"] = [
        dt.strftime("%Y-%m-%d %H:%M:%S") if dt is not None else None
        for dt in resolved_dates
    ]

    # Final columns to match DB schema
    required_cols = [
        "ticket_id", "priority", "status", "category",
        "subject", "description", "created_date",
        "resolved_date", "assigned_to"
    ]

    df = df[required_cols]

    df.to_sql(
        name=table_name,
        con=conn,
        if_exists="append",
        index=False
    )

    print(f"✅ Loaded {len(df)} IT tickets into '{table_name}'.")
    return len(df)
