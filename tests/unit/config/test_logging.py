"""Tests for logging configuration."""

import logging

from api.config.logging import get_logger, setup_logging


class TestLoggingConfig:
    """Brief test cases for logging configuration."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a proper logger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_setup_logging_configures_loggers(self, mocker):
        """Test that setup_logging configures the logging system."""
        mock_dict_config = mocker.patch("logging.config.dictConfig")
        mock_get_settings = mocker.patch("api.config.logging.get_settings")
        mock_get_settings.return_value.environment = "development"

        setup_logging()

        mock_dict_config.assert_called_once()
        config = mock_dict_config.call_args[0][0]
        assert config["version"] == 1
        assert "unified" in config["formatters"]
        assert "console" in config["handlers"]

    def test_setup_logging_production_log_level(self, mocker):
        """Test log level configuration for production environment."""
        mock_dict_config = mocker.patch("logging.config.dictConfig")
        mock_get_settings = mocker.patch("api.config.logging.get_settings")
        mock_get_settings.return_value.environment = "production"

        setup_logging()

        config = mock_dict_config.call_args[0][0]
        assert config["handlers"]["console"]["level"] == "INFO"

    def test_setup_logging_testing_log_level(self, mocker):
        """Test log level configuration for testing environment."""
        mock_dict_config = mocker.patch("logging.config.dictConfig")
        mock_get_settings = mocker.patch("api.config.logging.get_settings")
        mock_get_settings.return_value.environment = "testing"

        setup_logging()

        config = mock_dict_config.call_args[0][0]
        assert config["handlers"]["console"]["level"] == "WARNING"

    def test_setup_logging_sqlalchemy_handler_configuration(self, mocker):
        """Test that SQLAlchemy loggers are properly configured."""
        mocker.patch("logging.config.dictConfig")
        mock_get_logger = mocker.patch("logging.getLogger")
        mock_get_settings = mocker.patch("api.config.logging.get_settings")
        mock_get_settings.return_value.environment = "development"

        mock_logger = mocker.MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        setup_logging()

        # Verify SQLAlchemy loggers are configured
        assert mock_get_logger.call_count >= 2
        mock_logger.addHandler.assert_called()
        mock_logger.setLevel.assert_called()
