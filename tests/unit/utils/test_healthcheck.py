"""Tests for healthcheck utility."""

from sqlalchemy import text

from api.utils.healthcheck import (
    HealthCheckResponse,
    HealthStatus,
    ServiceStatus,
    perform_health_check,
)
from tests.conftest import mock_aiohttp_session


class TestHealthStatus:
    """Test cases for HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.UNHEALTHY == "unhealthy"


class TestServiceStatus:
    """Test cases for ServiceStatus enum."""

    def test_service_status_values(self):
        """Test ServiceStatus enum values."""
        assert ServiceStatus.OK == "ok"
        assert ServiceStatus.ERROR == "error"
        assert ServiceStatus.UNKNOWN == "unknown"


class TestHealthCheckResponse:
    """Test cases for HealthCheckResponse model."""

    def test_health_check_response_creation(self):
        """Test HealthCheckResponse model creation."""
        response = HealthCheckResponse(
            status=HealthStatus.HEALTHY,
            fastapi=ServiceStatus.OK,
            postgres=ServiceStatus.OK,
            swapi_external=ServiceStatus.OK,
        )

        assert response.status == HealthStatus.HEALTHY
        assert response.fastapi == ServiceStatus.OK
        assert response.postgres == ServiceStatus.OK
        assert response.swapi_external == ServiceStatus.OK

    def test_health_check_response_unhealthy(self):
        """Test HealthCheckResponse with unhealthy status."""
        response = HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            fastapi=ServiceStatus.OK,
            postgres=ServiceStatus.ERROR,
            swapi_external=ServiceStatus.OK,
        )

        assert response.status == HealthStatus.UNHEALTHY
        assert response.postgres == ServiceStatus.ERROR


class TestPerformHealthCheck:
    """Test cases for perform_health_check function."""

    async def test_perform_health_check_all_healthy(
        self, mock_db_session, mock_settings, mocker
    ):
        """Test health check when all services are healthy."""
        # Mock database query
        mock_result = mocker.MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_db_session.execute.return_value = mock_result

        # Mock HTTP response
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_aiohttp_session(mocker, mock_response)

        # Mock settings
        mocker.patch("api.utils.healthcheck.get_settings", return_value=mock_settings)

        result = await perform_health_check(mock_db_session)

        assert result.status == HealthStatus.HEALTHY
        assert result.fastapi == ServiceStatus.OK
        assert result.postgres == ServiceStatus.OK
        assert result.swapi_external == ServiceStatus.OK

        # Verify database was called
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0][0]
        assert isinstance(call_args, type(text("SELECT 1")))

    async def test_perform_health_check_database_error(
        self, mock_db_session, mock_settings, mocker
    ):
        """Test health check when database fails."""
        # Mock database exception
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        # Mock HTTP response (healthy)
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_aiohttp_session(mocker, mock_response)

        # Mock settings
        mocker.patch("api.utils.healthcheck.get_settings", return_value=mock_settings)

        result = await perform_health_check(mock_db_session)

        assert result.status == HealthStatus.UNHEALTHY
        assert result.fastapi == ServiceStatus.OK
        assert result.postgres == ServiceStatus.ERROR
        assert result.swapi_external == ServiceStatus.OK

    async def test_perform_health_check_swapi_error(
        self, mock_db_session, mock_settings, mocker
    ):
        """Test health check when SWAPI external service fails."""
        # Mock database query (healthy)
        mock_result = mocker.MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_db_session.execute.return_value = mock_result

        # Mock HTTP response with error status
        mock_response = mocker.MagicMock()
        mock_response.status = 500
        mock_aiohttp_session(mocker, mock_response)

        # Mock settings
        mocker.patch("api.utils.healthcheck.get_settings", return_value=mock_settings)

        result = await perform_health_check(mock_db_session)

        assert result.status == HealthStatus.UNHEALTHY
        assert result.fastapi == ServiceStatus.OK
        assert result.postgres == ServiceStatus.OK
        assert result.swapi_external == ServiceStatus.ERROR

    async def test_perform_health_check_swapi_exception(
        self, mock_db_session, mock_settings, mocker
    ):
        """Test health check when SWAPI request raises exception."""
        # Mock database query (healthy)
        mock_result = mocker.MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_db_session.execute.return_value = mock_result

        # Mock aiohttp to raise exception
        mock_session = mocker.AsyncMock()
        mock_session.__aenter__.side_effect = Exception("Network error")
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        # Mock settings
        mocker.patch("api.utils.healthcheck.get_settings", return_value=mock_settings)

        result = await perform_health_check(mock_db_session)

        assert result.status == HealthStatus.UNHEALTHY
        assert result.fastapi == ServiceStatus.OK
        assert result.postgres == ServiceStatus.OK
        assert result.swapi_external == ServiceStatus.ERROR

    async def test_perform_health_check_all_services_fail(
        self, mock_db_session, mock_settings, mocker
    ):
        """Test health check when all services fail."""
        # Mock database exception
        mock_db_session.execute.side_effect = Exception("Database error")

        # Mock aiohttp exception
        mock_session = mocker.AsyncMock()
        mock_session.__aenter__.side_effect = Exception("Network error")
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        # Mock settings
        mocker.patch("api.utils.healthcheck.get_settings", return_value=mock_settings)

        result = await perform_health_check(mock_db_session)

        assert result.status == HealthStatus.UNHEALTHY
        assert result.fastapi == ServiceStatus.OK
        assert result.postgres == ServiceStatus.ERROR
        assert result.swapi_external == ServiceStatus.ERROR

    async def test_perform_health_check_timeout_handling(
        self, mock_db_session, mock_settings, mocker
    ):
        """Test health check handles timeout correctly."""
        # Mock database query (healthy)
        mock_result = mocker.MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_db_session.execute.return_value = mock_result

        # Mock aiohttp ClientTimeout and session
        mock_timeout = mocker.patch("aiohttp.ClientTimeout")
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_aiohttp_session(mocker, mock_response)

        # Mock settings
        mocker.patch("api.utils.healthcheck.get_settings", return_value=mock_settings)

        result = await perform_health_check(mock_db_session)

        # Verify timeout was set correctly
        mock_timeout.assert_called_once_with(total=5.0)
        assert result.status == HealthStatus.HEALTHY
