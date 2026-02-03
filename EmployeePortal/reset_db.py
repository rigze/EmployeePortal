from app.database import engine
from sqlalchemy import text

print("Dropping tables using raw SQL...")
with engine.connect() as connection:
    # Disable foreign key checks to avoid ordering issues
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    tables = ["users", "employees", "salaries", "payslips"]
    for table in tables:
        try:
            print(f"Dropping table: {table}")
            connection.execute(text(f"DROP TABLE IF EXISTS {table};"))
        except Exception as e:
            print(f"Error dropping {table}: {e}")
            
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    print("Tables dropped.")
