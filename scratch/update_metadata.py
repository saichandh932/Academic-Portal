import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='student_performance_db'
    )
    cur = conn.cursor()
    
    # Update students with Vignan standard metadata
    sql = """
        UPDATE students 
        SET course = %s, 
            branch = %s, 
            year = %s, 
            semester = %s, 
            section = %s 
        WHERE (course IS NULL OR course = 'Unknown' OR course = 'N/A')
    """
    params = ('B.Tech', 'CSE', '2', '2', 'A')
    
    cur.execute(sql, params)
    conn.commit()
    
    print(f"Successfully updated {cur.rowcount} students with institutional metadata.")
    
except Exception as e:
    print(f"Error updating metadata: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cur.close()
        conn.close()
