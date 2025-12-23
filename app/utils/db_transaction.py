"""
Database Transaction Helper
Provides context manager for safe database transactions with automatic rollback and retry logic
"""
from contextlib import contextmanager
from app import db
from app.utils.unified_logger import get_logger
from sqlalchemy.exc import OperationalError, DisconnectionError
import time

logger = get_logger('DBTransaction')

# Transaction retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds
QUERY_TIMEOUT = 30  # seconds


@contextmanager
def db_transaction(retries: int = MAX_RETRIES, query_timeout: int = QUERY_TIMEOUT):
    """
    Context manager for database transactions with retry logic and query timeout.
    
    Automatically commits on success and rolls back on error.
    Retries on transient database errors.
    Ensures session is properly closed.
    
    Args:
        retries: Maximum number of retry attempts (default: 3)
        query_timeout: Query timeout in seconds (default: 30)
    
    Usage:
        with db_transaction() as session:
            transaction = Transaction(...)
            session.add(transaction)
            # Automatically commits on success
        
        # Automatically rolls back on error and retries on transient errors
    """
    attempt = 0
    last_error = None
    
    while attempt < retries:
        try:
            # Set query timeout if supported by database
            try:
                from flask import current_app
                db_type = current_app.config.get('DATABASE_TYPE', 'sqlite').lower()
                
                if db_type in ['postgresql', 'postgres']:
                    # PostgreSQL query timeout
                    db.session.execute(
                        db.text(f"SET statement_timeout = {query_timeout * 1000}")  # milliseconds
                    )
                elif db_type in ['mssql', 'sqlserver']:
                    # MSSQL query timeout
                    db.session.execute(
                        db.text(f"SET QUERY_GOVERNOR_COST_LIMIT {query_timeout * 100}")
                    )
                # SQLite doesn't support query timeout at session level
            except Exception as timeout_error:
                logger.debug(f"Could not set query timeout: {timeout_error}")
            
            yield db.session
            db.session.commit()
            logger.debug("Transaction committed successfully")
            return  # Success, exit retry loop
            
        except (OperationalError, DisconnectionError) as e:
            # Transient database error - retry
            attempt += 1
            last_error = e
            db.session.rollback()
            
            if attempt < retries:
                wait_time = RETRY_DELAY * attempt  # Exponential backoff
                logger.warning(
                    f"Database error (attempt {attempt}/{retries}): {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    f"Transaction failed after {retries} attempts: {str(e)}",
                    exc_info=True
                )
                raise
                
        except Exception as e:
            # Non-retryable error
            db.session.rollback()
            logger.error(f"Transaction rolled back due to error: {str(e)}", exc_info=True)
            raise
        finally:
            # Clean up session state
            if db.session.is_active:
                try:
                    db.session.expunge_all()
                except Exception:
                    pass
    
    # If we get here, all retries failed
    if last_error:
        raise last_error

