import psycopg2

try:
    print("Attempting to connect...")
    # This matches your main.py settings exactly
    conn = psycopg2.connect(
        dbname="sitetrack_db",
        user="postgres",
        password="admin123", 
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cur = conn.cursor()
    print("✅ Connected to sitetrack_db successfully!")

    # 1. NUKE THE OLD TABLE
    print("💥 Deleting old 'users' table...")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")

    # 2. CREATE THE FRESH TABLE (With the 'name' column!)
    print("🔨 Creating new 'users' table...")
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100), 
            phone_number VARCHAR(15) UNIQUE NOT NULL,
            password VARCHAR(50),
            role VARCHAR(50)
        );
    """)

    # 3. ADD THE USER
    print("👤 Adding Ramesh Site (9999999999)...")
    cur.execute("""
        INSERT INTO users (name, phone_number, password, role)
        VALUES ('Ramesh Site', '9999999999', 'pass123', 'Site Engineer');
    """)

    print("\n-----------------------------------------")
    print("✅ SUCCESS! The database is FIXED.")
    print("The 'name' column now 100% exists.")
    print("-----------------------------------------")

    cur.close()
    conn.close()

except Exception as e:
    print("\n❌ ERROR:", e)