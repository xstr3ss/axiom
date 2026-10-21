import logging
from typing import Any, Dict, Optional

class MasterLogger:
    def __init__(self, formatter: Optional[str] = None, database: Optional[Dict[str, Any]] = None):
        self.formatter = formatter
        self.database = database
        self.logger = logging.getLogger("MasterLogger")
        self.logger.setLevel(logging.INFO)
        
        if formatter:
            fmt = logging.Formatter(formatter)
        else:
            fmt = logging.Formatter()
        
        # To prevent duplicate handlers if called multiple times in tests or repeated initialization
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(fmt)
            self.logger.addHandler(handler)
        
        self._configure_database()

    def _configure_database(self):
        if self.database:
            # Simple stub for database configuration
            pass

def create_master_logger(formatter: Optional[str] = None, database: Optional[Dict[str, Any]] = None) -> None:
    """
    Creates a master logger module that uses a specified formatter and a database module.
    
    Parameters:
    formatter (Optional[str]): The format string for the logs. If None, no formatter is used.
    database (Optional[Dict[str, Any]]): The database configuration. If None, no database is used.
    
    Postconditions:
    - The master logger is created with the provided formatter and database configuration.
    - If no formatter or database is provided, the master logger is configured accordingly.
    
    Domain Constraints:
    - formatter and database can be either explicitly provided or None.
    - If formatter is provided, it should be a valid string format specifier.
    - If database is provided, it should be a dictionary with valid key-value pairs.
    
    Preconditions:
    - formatter is a non-empty string if provided.
    - database is a non-empty dictionary if provided.
    
    Returns:
    None
    """
    if formatter is not None and not isinstance(formatter, str):
        raise TypeError("formatter must be a string if provided")
    if formatter is not None and not formatter:
        raise ValueError("formatter must be a non-empty string if provided")
        
    if database is not None and not isinstance(database, dict):
        raise TypeError("database must be a dictionary if provided")
    if database is not None and not database:
        raise ValueError("database must be a non-empty dictionary if provided")
        
    MasterLogger(formatter, database)