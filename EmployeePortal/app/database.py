from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# !!! UPDATE WITH YOUR PASSWORD !!!
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Rigze03!@localhost/employee_portal"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency (This is used in other files to get a DB session)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
