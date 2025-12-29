import psycopg2

# --- CONFIGURATION ---
DB_HOST = "localhost"
DB_NAME = "sitetrack_db"
DB_USER = "postgres"
DB_PASS = "admin123"  # <--- MAKE SURE THIS IS YOUR PASSWORD

def create_tables():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()

        # 1. Create Users Table
        print("Creating Users Table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(15) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Insert Test User (Only if not exists)
        print("Adding Test User...")
        cur.execute("""
            INSERT INTO users (full_name, phone_number, password_hash, role) 
            VALUES ('Ramesh Site', '9999999999', 'pass123', 'SiteEngineer')
            ON CONFLICT (phone_number) DO NOTHING;
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ SUCCESS! Database is ready.")

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    create_tables()