import psycopg2

# THESE ARE THE EXACT CREDENTIALS FROM YOUR MAIN.PY
DB_HOST = "localhost"
DB_NAME = "sitetrack_db"
DB_USER = "postgres"
DB_PASS = "admin123"

def fix_database():
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(
            host=DB_HOST, 
            database=DB_NAME, 
            user=DB_USER, 
            password=DB_PASS
        )
        conn.autocommit = True
        cur = conn.cursor()

        # 1. FORCE CREATE PROJECTS TABLE
        print("🔨 Creating 'projects' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id SERIAL PRIMARY KEY,
                project_name VARCHAR(255) NOT NULL,
                location VARCHAR(255) NOT NULL
            );
        """)

        # 2. FORCE CREATE DWR_ENTRIES TABLE (To prevent the next error)
        print("🔨 Creating 'dwr_entries' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dwr_entries (
                entry_id SERIAL PRIMARY KEY,
                project_id INT,
                user_name VARCHAR(100),
                description TEXT,
                location_work VARCHAR(255),
                quantity VARCHAR(50),
                subcontractor VARCHAR(100),
                site_incharge VARCHAR(100),
                remarks TEXT,
                entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. INSERT DATA (Only if table is empty)
        cur.execute("SELECT COUNT(*) FROM projects")
        count = cur.fetchone()[0]
        
        if count == 0:
            print("📝 Inserting dummy projects...")
            cur.execute("""
                INSERT INTO projects (project_name, location) VALUES 
                ('Metro Station Phase 1', 'Chennai Central'),
                ('Highway Expansion', 'Bangalore North'),
                ('Tech Park Site B', 'Hyderabad');
            """)
        else:
            print(f"✅ Table already has {count} projects.")

        print("\n✅ SUCCESS! The database is strictly fixed.")
        conn.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Make sure your password is 'admin123' and database 'sitetrack_db' exists.")

if __name__ == "__main__":
    fix_database()