from passlib.context import CryptContext
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
# !!! IMPORTANT: Replace YOUR_MYSQL_PASSWORD with your actual Workbench password !!!
DATABASE_URL = "mysql+pymysql://root:Rigze03!@localhost/employee_portal"

# --- 1. SETUP HASHING ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
secret_password = "password123"

# --- 2. GENERATE NEW HASH ---
print(f"Generating hash for password: '{secret_password}'...")
new_hash = pwd_context.hash(secret_password)
print(f"New Hash: {new_hash}")

# --- 3. UPDATE DATABASE ---
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("Connecting to Database...")

        # Delete old admin (to avoid duplicates)
        connection.execute(text("DELETE FROM users WHERE username = 'admin'"))

        # Insert new admin with the PERFECT hash
        query = text(
            """
            INSERT INTO users (username, email, hashed_password, role) 
            VALUES ('admin', 'admin@company.com', :h, 'manager')
        """
        )
        connection.execute(query, {"h": new_hash})
        connection.commit()  # Save changes

    print("\nSUCCESS! User 'admin' has been reset.")
    print("You can now login with: password123")

except Exception as e:
    print(f"\nERROR: Could not connect to database.\n{e}")
    print("Did you update the 'YOUR_MYSQL_PASSWORD' in this script?")
