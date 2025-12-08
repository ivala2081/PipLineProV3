"""
Database Transaction Helper
Provides context manager for safe database transactions with automatic rollback
"""
from contextlib import contextmanager
from app import db
from app.utils.unified_logger import get_logger

logger = get_logger('DBTransaction')


@contextmanager
def db_transaction():
    """
    Context manager for database transactions.
    
    Automatically commits on success and rolls back on error.
    Ensures session is properly closed.
    
    Usage:
        with db_transaction() as session:
            transaction = Transaction(...)
            session.add(transaction)
            # Otomatik commit yapilir
        
        # Error durumunda otomatik rollback yapilir
    """
    try:
        yield db.session
        db.session.commit()
        logger.debug("Transaction committed successfully")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Transaction rolled back due to error: {str(e)}", exc_info=True)
        raise
    finally:
        # Session'i temizle ama kapatma (Flask-SQLAlchemy otomatik yonetir)
        # Sadece pending state'i kontrol et
        if db.session.is_active:
            try:
                db.session.expunge_all()
            except Exception:
                pass

