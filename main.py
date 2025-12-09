from app.data.db import connect_database
from app.data.schema import create_all_tables
from app.services.user_service import register_user, login_user, migrate_users_from_file
from app.data.incidents import insert_incident, get_all_incidents, load_csv_to_table_incidents, get_incidents_by_type_count, get_high_severity_by_status, get_incident_types_with_many_cases, update_incident_status, delete_incident
from pathlib import Path

def main():
    print("=" * 60)
    print("Week 8: Database Demo")
    print("=" * 60)
    
    # 1. Setup database
    conn = connect_database()
    create_all_tables(conn)
    # conn.close()
    
    # 2. Migrate users
    migrate_users_from_file(conn)
    
    # 3. Test authentication
    success, msg = register_user("kareena", "SecurePass123!", "analyst")
    print(msg)
    
    success, msg = login_user("kareena", "SecurePass123!")
    print(msg)
    
    # 4. Test CRUD
    incident_id = insert_incident(
        "2024-11-05",
        "Phishing",
        "High",
        "Open",
        "Suspicious email detected",
        "kareena"
    )
    print(f"Created incident #{incident_id}")
    
    # 5. Query data
    df = get_all_incidents()
    print(f"Total incidents: {len(df)}")

    load_csv_to_table_incidents(conn, Path("DATA") / "cyber_incidents.csv", "cyber_incidents")

    # 5. Query data again
    df = get_all_incidents()
    print(f"Total incidents: {len(df)}")

    print("\n Incidents by Type:")
    df_by_type = get_incidents_by_type_count(conn)
    print(df_by_type)

    print("\n High Severity Incidents by Status:")
    df_high_severity = get_high_severity_by_status(conn)
    print(df_high_severity)

    print("\n Incident Types with Many Cases (>5):")
    df_many_cases = get_incident_types_with_many_cases(conn, min_count=5)
    print(df_many_cases)

    # Test 2: CRUD Operations
    print("\n[TEST 2] CRUD Operations")
    
    # Create
    test_id = insert_incident( 
        "2024-11-05",
        "Test Incident",
        "Low",
        "Open",
        "This is a test incident",
        "test_user"
    )
    print(f"  Create: ✅ Incident #{test_id} created")
      
    # Update
    update_incident_status(conn, test_id, "Resolved")
    print(f"  Update:  Status updated")
    
    # Delete
    delete_incident(conn, test_id)
    print(f"  Delete:  Incident deleted")

    conn.close()

if __name__ == "__main__":
    main()
