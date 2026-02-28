import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

# Database Setup
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    # Import models here to ensure they are registered with Base
    from app import models
    from app.core.security import get_password_hash
    Base.metadata.create_all(bind=engine)
    
    # Seed Admin
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).filter(models.Admin.username == "admin").first()
        if not admin:
            logger.warning(
                "Seeding default admin user with password 'admin'. "
                "IMPORTANT: Change the admin password immediately after first login!"
            )
            db_admin = models.Admin(
                username="admin",
                password_hash=get_password_hash("admin")
            )
            db.add(db_admin)
            db.commit()
            logger.info("Admin user seeded (admin/admin)")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
