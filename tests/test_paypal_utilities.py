# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for PayPal utility functions and helpers.
"""

import pytest
from unittest.mock import patch, Mock
import requests


class TestPayPalUtilityFunctions:
    """Test PayPal utility functions in isolation."""

    def test_validate_paypal_configuration_valid_credentials(self):
        """Test PayPal configuration validation with valid credentials."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock successful PayPal API response
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "mock_token"}
            mock_post.return_value = mock_response

            result = validate_paypal_configuration("test_client_id", "test_secret", sandbox=True)

            assert result["valid"] is True
            assert "válida" in result["message"]
            
            # Verify correct API call
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert "sandbox" in args[0]  # Should use sandbox URL
            assert kwargs["auth"] == ("test_client_id", "test_secret")

    def test_validate_paypal_configuration_production_mode(self):
        """Test PayPal configuration validation in production mode."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock successful PayPal API response
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "prod_token"}
            mock_post.return_value = mock_response

            result = validate_paypal_configuration("prod_client_id", "prod_secret", sandbox=False)

            assert result["valid"] is True
            
            # Verify correct API call for production
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert "sandbox" not in args[0] or "api.paypal.com" in args[0]

    def test_validate_paypal_configuration_invalid_credentials(self):
        """Test PayPal configuration validation with invalid credentials."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock failed PayPal API response
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid credentials"
            mock_post.return_value = mock_response

            result = validate_paypal_configuration("invalid_id", "invalid_secret", sandbox=True)

            assert result["valid"] is False
            assert "Error de configuración" in result["message"]
            assert "Invalid credentials" in result["message"]

    def test_validate_paypal_configuration_network_timeout(self):
        """Test PayPal configuration validation with network timeout."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock network timeout
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            assert result["valid"] is False
            assert "Error al validar" in result["message"]
            assert "Request timed out" in result["message"]

    def test_validate_paypal_configuration_connection_error(self):
        """Test PayPal configuration validation with connection error."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock connection error
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            assert result["valid"] is False
            assert "Error al validar" in result["message"]

    def test_validate_paypal_configuration_ssl_error(self):
        """Test PayPal configuration validation with SSL error."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock SSL error
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.SSLError("SSL verification failed")

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            assert result["valid"] is False
            assert "Error al validar" in result["message"]

    def test_validate_paypal_configuration_malformed_response(self):
        """Test PayPal configuration validation with malformed response."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock response with invalid JSON
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_response

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            # Should still be considered valid if status is 200
            assert result["valid"] is True

    def test_validate_paypal_configuration_server_error(self):
        """Test PayPal configuration validation with server error."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock server error
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_post.return_value = mock_response

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            assert result["valid"] is False
            assert "Internal server error" in result["message"]

    def test_validate_paypal_configuration_missing_access_token(self):
        """Test PayPal configuration validation when access token is missing."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock response without access token
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"token_type": "Bearer", "expires_in": 3600}
            mock_post.return_value = mock_response

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            # Should still be considered valid if status is 200
            assert result["valid"] is True


class TestPayPalPaymentVerification:
    """Test PayPal payment verification utility functions."""

    def test_verify_paypal_payment_success_completed(self):
        """Test successful PayPal payment verification for completed order."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock successful verification response
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_order_id",
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "amount": {"value": "99.99", "currency_code": "USD"},
                        "description": "Test payment",
                    }
                ],
                "payer": {"payer_id": "test_payer_id"},
            }
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is True
            assert result["status"] == "COMPLETED"
            assert result["amount"] == "99.99"
            assert result["currency"] == "USD"
            assert result["payer_id"] == "test_payer_id"
            assert "order_data" in result

    def test_verify_paypal_payment_success_approved(self):
        """Test successful PayPal payment verification for approved order."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock verification response for approved payment
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_order_id",
                "status": "APPROVED",
                "purchase_units": [
                    {
                        "amount": {"value": "49.99", "currency_code": "EUR"},
                        "description": "European course payment",
                    }
                ],
                "payer": {"payer_id": "eur_payer_id"},
            }
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is True
            assert result["status"] == "APPROVED"
            assert result["amount"] == "49.99"
            assert result["currency"] == "EUR"

    def test_verify_paypal_payment_order_not_found(self):
        """Test PayPal payment verification for non-existent order."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock 404 response
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Order not found"
            mock_get.return_value = mock_response

            result = verify_paypal_payment("invalid_order_id", "mock_access_token")

            assert result["verified"] is False
            assert "error" in result
            assert "Payment verification failed" in result["error"]

    def test_verify_paypal_payment_unauthorized(self):
        """Test PayPal payment verification with unauthorized access token."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock 401 response
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "invalid_token")

            assert result["verified"] is False
            assert "error" in result

    def test_verify_paypal_payment_network_error(self):
        """Test PayPal payment verification with network error."""
        from now_lms.vistas.paypal import verify_paypal_payment

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is False
            assert "error" in result
            assert "Network error" in result["error"]

    def test_verify_paypal_payment_timeout(self):
        """Test PayPal payment verification with timeout."""
        from now_lms.vistas.paypal import verify_paypal_payment

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is False
            assert "error" in result

    def test_verify_paypal_payment_invalid_json(self):
        """Test PayPal payment verification with invalid JSON response."""
        from now_lms.vistas.paypal import verify_paypal_payment

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is False
            assert "error" in result

    def test_verify_paypal_payment_missing_purchase_units(self):
        """Test PayPal payment verification with missing purchase units."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock response with missing purchase_units
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_order_id",
                "status": "COMPLETED",
                # Missing purchase_units
                "payer": {"payer_id": "test_payer_id"},
            }
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is True  # Still verified if 200
            assert result["amount"] is None  # But amount is None
            assert result["currency"] is None

    def test_verify_paypal_payment_empty_purchase_units(self):
        """Test PayPal payment verification with empty purchase units."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock response with empty purchase_units
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_order_id",
                "status": "COMPLETED",
                "purchase_units": [],  # Empty list
                "payer": {"payer_id": "test_payer_id"},
            }
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is True
            assert result["amount"] is None
            assert result["currency"] is None

    def test_verify_paypal_payment_multiple_purchase_units(self):
        """Test PayPal payment verification with multiple purchase units."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock response with multiple purchase_units (should use first one)
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_order_id",
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "amount": {"value": "99.99", "currency_code": "USD"},
                        "description": "First item",
                    },
                    {
                        "amount": {"value": "49.99", "currency_code": "USD"},
                        "description": "Second item",
                    },
                ],
                "payer": {"payer_id": "test_payer_id"},
            }
            mock_get.return_value = mock_response

            result = verify_paypal_payment("test_order_id", "mock_access_token")

            assert result["verified"] is True
            assert result["amount"] == "99.99"  # Should use first purchase unit
            assert result["currency"] == "USD"


class TestPayPalConstants:
    """Test PayPal constants and configuration values."""

    def test_paypal_api_urls(self):
        """Test PayPal API URL constants."""
        from now_lms.vistas.paypal import PAYPAL_SANDBOX_API_URL, PAYPAL_PRODUCTION_API_URL

        assert PAYPAL_SANDBOX_API_URL == "https://api.sandbox.paypal.com"
        assert PAYPAL_PRODUCTION_API_URL == "https://api.paypal.com"

    def test_home_page_route_constant(self):
        """Test home page route constant."""
        from now_lms.vistas.paypal import HOME_PAGE_ROUTE

        assert HOME_PAGE_ROUTE == "home.pagina_de_inicio"


class TestPayPalErrorHandling:
    """Test PayPal error handling scenarios."""

    def test_verify_paypal_payment_with_different_error_codes(self):
        """Test PayPal payment verification with various HTTP error codes."""
        from now_lms.vistas.paypal import verify_paypal_payment

        error_codes = [400, 403, 422, 429, 500, 502, 503]

        for error_code in error_codes:
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = error_code
                mock_response.text = f"HTTP {error_code} Error"
                mock_get.return_value = mock_response

                result = verify_paypal_payment("test_order_id", "mock_access_token")

                assert result["verified"] is False, f"Should fail for HTTP {error_code}"
                assert "error" in result

    def test_validate_paypal_configuration_with_different_exceptions(self):
        """Test PayPal configuration validation with various exception types."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        exceptions = [
            requests.exceptions.RequestException("General request error"),
            requests.exceptions.HTTPError("HTTP error"),
            requests.exceptions.URLRequired("URL required"),
            requests.exceptions.TooManyRedirects("Too many redirects"),
            Exception("Generic exception"),
        ]

        for exception in exceptions:
            with patch("requests.post") as mock_post:
                mock_post.side_effect = exception

                result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

                assert result["valid"] is False
                assert "Error al validar" in result["message"]


class TestPayPalSecurityValidation:
    """Test PayPal security and input validation."""

    def test_verify_paypal_payment_with_malicious_order_id(self):
        """Test PayPal payment verification with malicious order ID."""
        from now_lms.vistas.paypal import verify_paypal_payment

        malicious_ids = [
            "'; DROP TABLE payments; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "null",
            "",
            "a" * 1000,  # Very long ID
        ]

        for malicious_id in malicious_ids:
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 404
                mock_response.text = "Order not found"
                mock_get.return_value = mock_response

                result = verify_paypal_payment(malicious_id, "mock_access_token")

                # Should handle safely without crashing
                assert result["verified"] is False
                assert "error" in result

    def test_validate_paypal_configuration_with_empty_credentials(self):
        """Test PayPal configuration validation with empty credentials."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        empty_credentials = ["", None, "   ", "\t\n"]

        for client_id in empty_credentials:
            for client_secret in empty_credentials:
                with patch("requests.post") as mock_post:
                    mock_post.side_effect = requests.exceptions.RequestException("Invalid auth")

                    result = validate_paypal_configuration(client_id, client_secret, sandbox=True)

                    assert result["valid"] is False
                    assert "Error al validar" in result["message"]