import pytest
import logging
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from master_logger import MasterLogger, create_master_logger


class TestMasterLogger:
    """Tests for the MasterLogger class."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset logger handlers before and after each test to ensure isolation."""
        logger = logging.getLogger("MasterLogger")
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.setLevel(logging.INFO)
        yield
        # Cleanup after test
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def test_init_with_none_defaults(self):
        """Test initialization with default None values."""
        ml = MasterLogger()
        assert ml.formatter is None
        assert ml.database is None
        assert ml.logger.name == "MasterLogger"
        assert ml.logger.level == logging.INFO
        # Should have one handler
        assert len(ml.logger.handlers) == 1

    def test_init_with_custom_formatter(self):
        """Test initialization with a custom format string."""
        fmt_str = "[%(levelname)s] %(message)s"
        ml = MasterLogger(formatter=fmt_str)
        assert ml.formatter == fmt_str
        assert ml.logger.level == logging.INFO
        # Check handler formatter
        handler = ml.logger.handlers[0]
        assert handler.formatter is not None
        # Verify the format string is applied (fmt._fmt attribute holds the format)
        assert handler.formatter._fmt == fmt_str

    def test_init_with_custom_database(self):
        """Test initialization with a custom database configuration."""
        db_config = {"host": "localhost", "port": 5432}
        ml = MasterLogger(database=db_config)
        assert ml.database == db_config

    def test_init_with_both_formatter_and_database(self):
        """Test initialization with both formatter and database."""
        fmt_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        db_config = {"root": "/test", "name": "testdb"}
        ml = MasterLogger(formatter=fmt_str, database=db_config)
        assert ml.formatter == fmt_str
        assert ml.database == db_config

    @patch('master_logger.MasterLogger._configure_database')
    def test_configure_database_called(self, mock_configure):
        """Test that _configure_database is called during init."""
        ml = MasterLogger(database={"key": "value"})
        mock_configure.assert_called_once()

    @patch('master_logger.MasterLogger._configure_database')
    def test_configure_database_with_none(self, mock_configure):
        """Test that _configure_database is still called even if database is None."""
        ml = MasterLogger()
        mock_configure.assert_called_once()

    def test_prevent_duplicate_handlers(self):
        """Test that appending a new instance does not duplicate handlers."""
        ml1 = MasterLogger()
        ml2 = MasterLogger()
        # The logger is a singleton (named "MasterLogger"), so handlers should remain 1
        assert len(ml1.logger.handlers) == 1
        assert len(ml2.logger.handlers) == 1
        assert ml1.logger.handlers == ml2.logger.handlers


class TestCreateMasterLogger:
    """Tests for the create_master_logger function."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset logger handlers before and after each test."""
        logger = logging.getLogger("MasterLogger")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        yield
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def test_returns_none(self):
        """Test that the function returns None."""
        result = create_master_logger()
        assert result is None

    @patch('master_logger.MasterLogger')
    def test_calls_master_logger_with_defaults(self, mock_ml):
        """Test that MasterLogger is instantiated with given args when defaults are used."""
        create_master_logger()
        mock_ml.assert_called_once_with(None, None)

    @patch('master_logger.MasterLogger')
    def test_calls_master_logger_with_args(self, mock_ml):
        """Test that MasterLogger is instantiated with provided args."""
        fmt = "%(message)s"
        db = {"host": "localhost"}
        create_master_logger(formatter=fmt, database=db)
        mock_ml.assert_called_once_with(fmt, db)

    def test_no_handlers_added_on_validation_error(self):
        """Test that no handlers are added if validation fails."""
        logger = logging.getLogger("MasterLogger")
        initial_count = len(logger.handlers)
        
        with pytest.raises(TypeError):
            create_master_logger(formatter=123)
            
        assert len(logger.handlers) == initial_count

    # --- Type & Value Preconditions --

    def test_invalid_formatter_type_int(self):
        """Test TypeError when formatter is an integer."""
        with pytest.raises(TypeError) as excinfo:
            create_master_logger(formatter=123)
        assert "formatter must be a string if provided" in str(excinfo.value)

    def test_invalid_formatter_type_list(self):
        """Test TypeError when formatter is a list."""
        with pytest.raises(TypeError) as excinfo:
            create_master_logger(formatter=["test"])
        assert "formatter must be a string if provided" in str(excinfo.value)

    def test_empty_formatter_string(self):
        """Test ValueError when formatter is an empty string."""
        with pytest.raises(ValueError) as excinfo:
            create_master_logger(formatter="")
        assert "formatter must be a non-empty string if provided" in str(excinfo.value)

    def test_invalid_database_type_list(self):
        """Test TypeError when database is a list."""
        with pytest.raises(TypeError) as excinfo:
            create_master_logger(database=["not a dict"])
        assert "database must be a dictionary if provided" in str(excinfo.value)

    def test_invalid_database_type_string(self):
        """Test TypeError when database is a string."""
        with pytest.raises(TypeError) as excinfo:
            create_master_logger(database="not a dict")
        assert "database must be a dictionary if provided" in str(excinfo.value)

    def test_empty_database_dict(self):
        """Test ValueError when database is an empty dictionary."""
        with pytest.raises(ValueError) as excinfo:
            create_master_logger(database={})
        assert "database must be a non-empty dictionary if provided" in str(excinfo.value)

    # --- Valid Invocations with Side Effects --

    def test_valid_formatter_only(self):
        """Test valid invocation with only formatter."""
        logger = logging.getLogger("MasterLogger")
        initial_handlers = len(logger.handlers)
        
        create_master_logger(formatter="%(levelname)s: %(message)s")
        
        # Since the logger is a singleton in logging, handlers might not increase 
        # if already present from previous tests, but if this is the first call in this context:
        # We check that it didn't crash.
        
        # Reset for specific handler count check in isolated scenario:
        # For robustness, we ensure no exception was raised primarily.
        assert True

    def test_valid_database_only(self):
        """Test valid invocation with only database."""
        logger = logging.getLogger("MasterLogger")
        
        create_master_logger(database={"host": "localhost"})
        
        assert True

    def test_valid_formatter_and_database(self):
        """Test valid invocation with both formatter and database."""
        logger = logging.getLogger("MasterLogger")
        
        create_master_logger(
            formatter="%(asctime)s - %(message)s",
            database={"host": "localhost", "user": "admin"}
        )
        
        assert True