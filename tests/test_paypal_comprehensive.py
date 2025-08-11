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
Comprehensive test cases for PayPal integration functionality.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import json
import requests


@pytest.fixture
def app_with_paypal_data(full_db_setup):
    """Application with PayPal configuration and test data."""
    from now_lms import database
    from now_lms.db import Usuario, Curso, PaypalConfig, Configuracion
    from now_lms.auth import proteger_secreto
    from now_lms.cache import cache

    with full_db_setup.app_context():
        # Clear cache before each test
        cache.clear()
        
        # Ensure configuration exists for proteger_secreto to work
        config = database.session.execute(database.select(Configuracion)).first()
        if not config:
            site_config = Configuracion(
                titulo="Test LMS",
                descripcion="Test Learning Management System",
                moneda="USD",
            )
            database.session.add(site_config)
            database.session.commit()
        else:
            config[0].moneda = "USD"
            database.session.commit()
        
        # Create PayPal configuration
        existing_paypal = database.session.execute(database.select(PaypalConfig)).first()
        if not existing_paypal:
            paypal_config = PaypalConfig(
                enable=True,
                sandbox=True,
                paypal_id="live_client_id_test",
                paypal_sandbox="sandbox_client_id_test",
            )
            paypal_config.paypal_secret = proteger_secreto("live_secret_test")
            paypal_config.paypal_sandbox_secret = proteger_secreto("sandbox_secret_test")
            database.session.add(paypal_config)
        else:
            existing_paypal[0].enable = True
            existing_paypal[0].sandbox = True
            existing_paypal[0].paypal_id = "live_client_id_test"
            existing_paypal[0].paypal_sandbox = "sandbox_client_id_test"

        # Create test user if not exists
        existing_user = database.session.execute(
            database.select(Usuario).where(Usuario.usuario == "test_paypal_user")
        ).first()
        
        if not existing_user:
            user = Usuario(
                usuario="test_paypal_user",
                acceso=proteger_secreto("test_password"),
                nombre="PayPal",
                apellido="Tester",
                correo_electronico="paypal@test.com",
                activo=True,
                tipo="student",
            )
            database.session.add(user)

        # Create test courses
        paid_course = Curso(
            nombre="Premium PayPal Course",
            codigo="PAYPAL001",
            descripcion="Test premium course with PayPal payment",
            descripcion_corta="Premium course",
            pagado=True,
            precio=99.99,
            publico=True,
            estado="open",
        )
        database.session.add(paid_course)

        expensive_course = Curso(
            nombre="Expensive PayPal Course",
            codigo="PAYPAL002",
            descripcion="Test expensive course",
            descripcion_corta="Expensive course",
            pagado=True,
            precio=999.99,
            publico=True,
            estado="open",
        )
        database.session.add(expensive_course)

        auditable_course = Curso(
            nombre="Auditable PayPal Course",
            codigo="PAYPAL003",
            descripcion="Test auditable course",
            descripcion_corta="Auditable course",
            pagado=True,
            auditable=True,
            precio=49.99,
            publico=True,
            estado="open",
        )
        database.session.add(auditable_course)

        database.session.commit()

        yield full_db_setup


class TestPayPalConfiguration:
    """Test PayPal configuration and validation."""

    def test_check_paypal_enabled_returns_true_when_enabled(self, app_with_paypal_data):
        """Test that check_paypal_enabled returns True when PayPal is enabled."""
        from now_lms.vistas.paypal import check_paypal_enabled

        with app_with_paypal_data.app_context():
            with app_with_paypal_data.test_request_context():
                result = check_paypal_enabled()
                assert result is True

    def test_check_paypal_enabled_returns_false_when_disabled(self, app_with_paypal_data):
        """Test that check_paypal_enabled returns False when PayPal is disabled."""
        from now_lms.vistas.paypal import check_paypal_enabled
        from now_lms import database
        from now_lms.db import PaypalConfig
        from now_lms.cache import cache

        with app_with_paypal_data.app_context():
            with app_with_paypal_data.test_request_context():
                # Clear cache first
                cache.clear()
                
                # Disable PayPal
                config = database.session.execute(database.select(PaypalConfig)).first()[0]
                config.enable = False
                database.session.commit()

                result = check_paypal_enabled()
                assert result is False

    def test_get_site_currency_returns_configured_currency(self, app_with_paypal_data):
        """Test that get_site_currency returns the configured currency."""
        from now_lms.vistas.paypal import get_site_currency

        with app_with_paypal_data.app_context():
            with app_with_paypal_data.test_request_context():
                currency = get_site_currency()
                assert currency == "USD"

    def test_get_site_currency_returns_default_when_not_configured(self, app_with_paypal_data):
        """Test that get_site_currency returns USD when no currency is configured."""
        from now_lms.vistas.paypal import get_site_currency
        from now_lms import database
        from now_lms.db import Configuracion
        from now_lms.cache import cache

        with app_with_paypal_data.app_context():
            with app_with_paypal_data.test_request_context():
                # Clear cache first
                cache.clear()
                
                # Remove currency configuration
                config = database.session.execute(database.select(Configuracion)).first()[0]
                config.moneda = None
                database.session.commit()

                currency = get_site_currency()
                assert currency == "USD"

    def test_validate_paypal_configuration_with_valid_credentials(self, app_with_paypal_data):
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

    def test_validate_paypal_configuration_with_invalid_credentials(self, app_with_paypal_data):
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

    def test_validate_paypal_configuration_with_network_error(self, app_with_paypal_data):
        """Test PayPal configuration validation with network error."""
        from now_lms.vistas.paypal import validate_paypal_configuration

        # Mock network error
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")

            result = validate_paypal_configuration("test_id", "test_secret", sandbox=True)

            assert result["valid"] is False
            assert "Error al validar" in result["message"]


class TestPayPalAccessToken:
    """Test PayPal access token management."""

    def test_get_paypal_access_token_success_sandbox(self, app_with_paypal_data):
        """Test successful access token retrieval in sandbox mode."""
        from now_lms.vistas.paypal import get_paypal_access_token

        # Mock successful PayPal API response and decryption
        with (
            patch("requests.post") as mock_post,
            patch("now_lms.auth.descifrar_secreto") as mock_decrypt,
        ):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "sandbox_access_token_123",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            mock_post.return_value = mock_response
            mock_decrypt.return_value = b"sandbox_secret_test"

            with app_with_paypal_data.app_context():
                token = get_paypal_access_token()
                assert token == "sandbox_access_token_123"

    def test_get_paypal_access_token_success_production(self, app_with_paypal_data):
        """Test successful access token retrieval in production mode."""
        from now_lms.vistas.paypal import get_paypal_access_token
        from now_lms import database
        from now_lms.db import PaypalConfig

        # Switch to production mode
        with app_with_paypal_data.app_context():
            config = database.session.execute(database.select(PaypalConfig)).first()[0]
            config.sandbox = False
            database.session.commit()

            # Mock successful PayPal API response and decryption
            with (
                patch("requests.post") as mock_post,
                patch("now_lms.auth.descifrar_secreto") as mock_decrypt,
            ):
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "production_access_token_456",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                }
                mock_post.return_value = mock_response
                mock_decrypt.return_value = b"live_secret_test"

                token = get_paypal_access_token()
                assert token == "production_access_token_456"

    def test_get_paypal_access_token_api_error(self, app_with_paypal_data):
        """Test access token retrieval with API error."""
        from now_lms.vistas.paypal import get_paypal_access_token

        # Mock failed PayPal API response
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid client credentials"
            mock_post.return_value = mock_response

            with app_with_paypal_data.app_context():
                token = get_paypal_access_token()
                assert token is None

    def test_get_paypal_access_token_no_config(self, app_with_paypal_data):
        """Test access token retrieval when no PayPal config exists."""
        from now_lms.vistas.paypal import get_paypal_access_token
        from now_lms import initial_setup
        from now_lms.db import eliminar_base_de_datos_segura

        with app_with_paypal_data.app_context():
            eliminar_base_de_datos_segura()
            initial_setup()

            token = get_paypal_access_token()
            assert token is None

    def test_get_paypal_access_token_missing_credentials(self, app_with_paypal_data):
        """Test access token retrieval with missing credentials."""
        from now_lms.vistas.paypal import get_paypal_access_token
        from now_lms import database
        from now_lms.db import PaypalConfig

        with app_with_paypal_data.app_context():
            # Clear credentials
            config = database.session.execute(database.select(PaypalConfig)).first()[0]
            config.paypal_sandbox = None
            config.paypal_sandbox_secret = None
            database.session.commit()

            token = get_paypal_access_token()
            assert token is None

    def test_get_paypal_access_token_decrypt_error(self, app_with_paypal_data):
        """Test access token retrieval with decryption error."""
        from now_lms.vistas.paypal import get_paypal_access_token
        from now_lms import database
        from now_lms.db import PaypalConfig

        with app_with_paypal_data.app_context():
            # Set invalid encrypted secret
            config = database.session.execute(database.select(PaypalConfig)).first()[0]
            config.paypal_sandbox_secret = b"invalid_encrypted_data"
            database.session.commit()

            with patch("now_lms.auth.descifrar_secreto") as mock_decrypt:
                mock_decrypt.side_effect = Exception("Decryption failed")

                token = get_paypal_access_token()
                assert token is None

    def test_get_paypal_access_token_network_timeout(self, app_with_paypal_data):
        """Test access token retrieval with network timeout."""
        from now_lms.vistas.paypal import get_paypal_access_token

        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

            with app_with_paypal_data.app_context():
                token = get_paypal_access_token()
                assert token is None


class TestPayPalPaymentVerification:
    """Test PayPal payment verification."""

    def test_verify_paypal_payment_success(self, app_with_paypal_data):
        """Test successful PayPal payment verification."""
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

            with app_with_paypal_data.app_context():
                result = verify_paypal_payment("test_order_id", "mock_access_token")

                assert result["verified"] is True
                assert result["status"] == "COMPLETED"
                assert result["amount"] == "99.99"
                assert result["currency"] == "USD"
                assert result["payer_id"] == "test_payer_id"

    def test_verify_paypal_payment_failed(self, app_with_paypal_data):
        """Test failed PayPal payment verification."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock failed verification response
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Order not found"
            mock_get.return_value = mock_response

            with app_with_paypal_data.app_context():
                result = verify_paypal_payment("invalid_order_id", "mock_access_token")

                assert result["verified"] is False
                assert "error" in result

    def test_verify_paypal_payment_network_error(self, app_with_paypal_data):
        """Test PayPal payment verification with network error."""
        from now_lms.vistas.paypal import verify_paypal_payment

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

            with app_with_paypal_data.app_context():
                result = verify_paypal_payment("test_order_id", "mock_access_token")

                assert result["verified"] is False
                assert "error" in result

    def test_verify_paypal_payment_invalid_response(self, app_with_paypal_data):
        """Test PayPal payment verification with invalid response format."""
        from now_lms.vistas.paypal import verify_paypal_payment

        # Mock response with missing required fields
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "test_order_id",
                # Missing status, purchase_units, etc.
            }
            mock_get.return_value = mock_response

            with app_with_paypal_data.app_context():
                result = verify_paypal_payment("test_order_id", "mock_access_token")

                assert result["verified"] is True  # Still considers it verified if 200
                assert result["status"] is None
                assert result["amount"] is None


class TestPayPalPaymentConfirmation:
    """Test PayPal payment confirmation endpoint."""

    def test_confirm_payment_success(self, app_with_paypal_data):
        """Test successful payment confirmation."""
        from now_lms import database
        from now_lms.db import Usuario, Pago, EstudianteCurso

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Mock PayPal API calls
            with (
                patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
                patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
                patch("now_lms.vistas.courses._crear_indice_avance_curso") as mock_progress,
            ):

                mock_token.return_value = "mock_access_token"
                mock_verify.return_value = {
                    "verified": True,
                    "status": "COMPLETED",
                    "amount": "99.99",
                    "currency": "USD",
                    "payer_id": "test_payer_id",
                }

                with app_with_paypal_data.test_client() as client:
                    # Login as test user
                    with client.session_transaction() as sess:
                        sess["_user_id"] = user.id
                        sess["_fresh"] = True

                    # Send payment confirmation
                    response = client.post(
                        "/paypal_checkout/confirm_payment",
                        data=json.dumps(
                            {
                                "orderID": "test_order_123",
                                "payerID": "test_payer_id",
                                "courseCode": "PAYPAL001",
                                "amount": 99.99,
                                "currency": "USD",
                            }
                        ),
                        content_type="application/json",
                    )

                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data["success"] is True
                    assert "exitosamente" in data["message"]

                    # Verify payment record was created
                    payment = database.session.execute(
                        database.select(Pago).filter_by(usuario=user.usuario, curso="PAYPAL001")
                    ).first()
                    assert payment is not None
                    payment = payment[0]
                    assert payment.estado == "completed"
                    assert float(payment.monto) == 99.99
                    assert payment.metodo == "paypal"
                    assert payment.referencia == "test_order_123"

                    # Verify enrollment was created
                    enrollment = database.session.execute(
                        database.select(EstudianteCurso).filter_by(usuario=user.usuario, curso="PAYPAL001")
                    ).first()
                    assert enrollment is not None
                    enrollment = enrollment[0]
                    assert enrollment.vigente is True

    def test_confirm_payment_missing_data(self, app_with_paypal_data):
        """Test payment confirmation with missing data."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                # Send incomplete payment data
                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(
                        {
                            "orderID": "test_order_123",
                            # Missing payerID, courseCode, amount
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 400
                data = json.loads(response.data)
                assert data["success"] is False
                assert "Missing required payment data" in data["error"]

    def test_confirm_payment_invalid_amount(self, app_with_paypal_data):
        """Test payment confirmation with invalid amount."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                # Send invalid amount
                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(
                        {
                            "orderID": "test_order_123",
                            "payerID": "test_payer_id",
                            "courseCode": "PAYPAL001",
                            "amount": -50.00,  # Negative amount
                            "currency": "USD",
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 400
                data = json.loads(response.data)
                assert data["success"] is False
                assert "Invalid payment amount" in data["error"]

    def test_confirm_payment_verification_failed(self, app_with_paypal_data):
        """Test payment confirmation when PayPal verification fails."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Mock failed PayPal verification
            with (
                patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
                patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
            ):

                mock_token.return_value = "mock_access_token"
                mock_verify.return_value = {
                    "verified": False,
                    "error": "Payment verification failed",
                }

                with app_with_paypal_data.test_client() as client:
                    # Login as test user
                    with client.session_transaction() as sess:
                        sess["_user_id"] = user.id
                        sess["_fresh"] = True

                    response = client.post(
                        "/paypal_checkout/confirm_payment",
                        data=json.dumps(
                            {
                                "orderID": "test_order_123",
                                "payerID": "test_payer_id",
                                "courseCode": "PAYPAL001",
                                "amount": 99.99,
                                "currency": "USD",
                            }
                        ),
                        content_type="application/json",
                    )

                    assert response.status_code == 400
                    data = json.loads(response.data)
                    assert data["success"] is False
                    assert "Payment verification failed" in data["error"]

    def test_confirm_payment_amount_mismatch(self, app_with_paypal_data):
        """Test payment confirmation with amount mismatch."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Mock PayPal verification with different amount
            with (
                patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
                patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
            ):

                mock_token.return_value = "mock_access_token"
                mock_verify.return_value = {
                    "verified": True,
                    "status": "COMPLETED",
                    "amount": "50.00",  # Different from expected 99.99
                    "currency": "USD",
                    "payer_id": "test_payer_id",
                }

                with app_with_paypal_data.test_client() as client:
                    # Login as test user
                    with client.session_transaction() as sess:
                        sess["_user_id"] = user.id
                        sess["_fresh"] = True

                    response = client.post(
                        "/paypal_checkout/confirm_payment",
                        data=json.dumps(
                            {
                                "orderID": "test_order_123",
                                "payerID": "test_payer_id",
                                "courseCode": "PAYPAL001",
                                "amount": 99.99,
                                "currency": "USD",
                            }
                        ),
                        content_type="application/json",
                    )

                    assert response.status_code == 400
                    data = json.loads(response.data)
                    assert data["success"] is False
                    assert "Payment amount mismatch" in data["error"]

    def test_confirm_payment_duplicate_payment(self, app_with_paypal_data):
        """Test payment confirmation for already processed payment."""
        from now_lms import database
        from now_lms.db import Usuario, Pago

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Create existing completed payment
            existing_payment = Pago(
                usuario=user.usuario,
                curso="PAYPAL001",
                nombre=user.nombre,
                apellido=user.apellido,
                correo_electronico=user.correo_electronico,
                referencia="test_order_123",
                monto=99.99,
                moneda="USD",
                metodo="paypal",
                estado="completed",
            )
            database.session.add(existing_payment)
            database.session.commit()

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(
                        {
                            "orderID": "test_order_123",
                            "payerID": "test_payer_id",
                            "courseCode": "PAYPAL001",
                            "amount": 99.99,
                            "currency": "USD",
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["success"] is True
                assert "ya procesado" in data["message"]

    def test_confirm_payment_no_access_token(self, app_with_paypal_data):
        """Test payment confirmation when access token retrieval fails."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Mock failed access token retrieval
            with patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token:
                mock_token.return_value = None

                with app_with_paypal_data.test_client() as client:
                    # Login as test user
                    with client.session_transaction() as sess:
                        sess["_user_id"] = user.id
                        sess["_fresh"] = True

                    response = client.post(
                        "/paypal_checkout/confirm_payment",
                        data=json.dumps(
                            {
                                "orderID": "test_order_123",
                                "payerID": "test_payer_id",
                                "courseCode": "PAYPAL001",
                                "amount": 99.99,
                                "currency": "USD",
                            }
                        ),
                        content_type="application/json",
                    )

                    assert response.status_code == 500
                    data = json.loads(response.data)
                    assert data["success"] is False
                    assert "PayPal configuration error" in data["error"]

    def test_confirm_payment_course_not_found(self, app_with_paypal_data):
        """Test payment confirmation for non-existent course."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Mock PayPal API calls
            with (
                patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
                patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
            ):

                mock_token.return_value = "mock_access_token"
                mock_verify.return_value = {
                    "verified": True,
                    "status": "COMPLETED",
                    "amount": "99.99",
                    "currency": "USD",
                    "payer_id": "test_payer_id",
                }

                with app_with_paypal_data.test_client() as client:
                    # Login as test user
                    with client.session_transaction() as sess:
                        sess["_user_id"] = user.id
                        sess["_fresh"] = True

                    response = client.post(
                        "/paypal_checkout/confirm_payment",
                        data=json.dumps(
                            {
                                "orderID": "test_order_123",
                                "payerID": "test_payer_id",
                                "courseCode": "NONEXISTENT",  # Non-existent course
                                "amount": 99.99,
                                "currency": "USD",
                            }
                        ),
                        content_type="application/json",
                    )

                    assert response.status_code == 404
                    data = json.loads(response.data)
                    assert data["success"] is False
                    assert "Course not found" in data["error"]


class TestPayPalUtilityEndpoints:
    """Test PayPal utility endpoints."""

    def test_get_client_id_sandbox_mode(self, app_with_paypal_data):
        """Test getting client ID in sandbox mode."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/get_client_id")

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["client_id"] == "sandbox_client_id_test"
                assert data["sandbox"] is True
                assert data["currency"] == "USD"

    def test_get_client_id_production_mode(self, app_with_paypal_data):
        """Test getting client ID in production mode."""
        from now_lms import database
        from now_lms.db import Usuario, PaypalConfig

        with app_with_paypal_data.app_context():
            # Switch to production mode
            config = database.session.execute(database.select(PaypalConfig)).first()[0]
            config.sandbox = False
            database.session.commit()

            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/get_client_id")

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["client_id"] == "live_client_id_test"
                assert data["sandbox"] is False
                assert data["currency"] == "USD"

    def test_payment_status_endpoint(self, app_with_paypal_data):
        """Test payment status endpoint."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/payment_status/PAYPAL001")

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["course_code"] == "PAYPAL001"
                assert data["course_name"] == "Premium PayPal Course"
                assert data["course_paid"] is True
                assert data["course_price"] == 99.99
                assert data["enrolled"] is False
                assert data["site_currency"] == "USD"

    def test_debug_config_endpoint_admin(self, app_with_paypal_data):
        """Test debug config endpoint as admin."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            admin = database.session.execute(database.select(Usuario).filter_by(usuario="admin_paypal")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as admin
                with client.session_transaction() as sess:
                    sess["_user_id"] = admin.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/debug_config")

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["paypal_enabled"] is True
                assert data["sandbox_mode"] is True
                assert data["client_id_configured"] is True
                assert data["sandbox_client_id_configured"] is True
                assert data["site_currency"] == "USD"

    def test_debug_config_endpoint_non_admin(self, app_with_paypal_data):
        """Test debug config endpoint as non-admin (should be forbidden)."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as regular user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/debug_config")

                # Should be forbidden for non-admin users
                assert response.status_code in [403, 302]  # 403 forbidden or 302 redirect


class TestPayPalPaymentPage:
    """Test PayPal payment page functionality."""

    def test_payment_page_valid_course(self, app_with_paypal_data):
        """Test PayPal payment page for valid paid course."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/payment/PAYPAL001")

                assert response.status_code == 200
                # Check that the payment template is rendered
                assert b"Premium PayPal Course" in response.data or b"paypal" in response.data.lower()

    def test_payment_page_free_course(self, app_with_paypal_data):
        """Test PayPal payment page redirects for free course."""
        from now_lms import database
        from now_lms.db import Usuario, Curso

        with app_with_paypal_data.app_context():
            # Create a free course
            free_course = Curso(
                nombre="Free Test Course",
                codigo="FREE001",
                descripcion="Test free course",
                descripcion_corta="Free course",
                pagado=False,
                precio=0,
                publico=True,
                estado="open",
            )
            database.session.add(free_course)
            database.session.commit()

            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/payment/FREE001")

                # Should redirect away from PayPal payment page
                assert response.status_code == 302

    def test_payment_page_nonexistent_course(self, app_with_paypal_data):
        """Test PayPal payment page for non-existent course."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/payment/NONEXISTENT")

                # Should redirect with error
                assert response.status_code == 302

    def test_payment_page_paypal_disabled(self, app_with_paypal_data):
        """Test PayPal payment page when PayPal is disabled."""
        from now_lms import database
        from now_lms.db import Usuario, PaypalConfig

        with app_with_paypal_data.app_context():
            # Disable PayPal
            config = database.session.execute(database.select(PaypalConfig)).first()[0]
            config.enable = False
            database.session.commit()

            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/payment/PAYPAL001")

                # Should redirect with error when PayPal is disabled
                assert response.status_code == 302


class TestPayPalEdgeCases:
    """Test PayPal edge cases and error scenarios."""

    def test_confirm_payment_with_empty_request_body(self, app_with_paypal_data):
        """Test payment confirmation with empty request body."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data="",
                    content_type="application/json",
                )

                assert response.status_code == 400
                data = json.loads(response.data)
                assert data["success"] is False
                assert "No payment data received" in data["error"]

    def test_confirm_payment_with_string_amount(self, app_with_paypal_data):
        """Test payment confirmation with string amount."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(
                        {
                            "orderID": "test_order_123",
                            "payerID": "test_payer_id",
                            "courseCode": "PAYPAL001",
                            "amount": "invalid_amount",  # Invalid string
                            "currency": "USD",
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 400
                data = json.loads(response.data)
                assert data["success"] is False
                assert "Invalid payment amount" in data["error"]

    def test_resume_payment_valid(self, app_with_paypal_data):
        """Test resuming a valid pending payment."""
        from now_lms import database
        from now_lms.db import Usuario, Pago

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Create pending payment
            pending_payment = Pago(
                usuario=user.usuario,
                curso="PAYPAL001",
                nombre=user.nombre,
                apellido=user.apellido,
                correo_electronico=user.correo_electronico,
                monto=99.99,
                moneda="USD",
                metodo="paypal",
                estado="pending",
            )
            database.session.add(pending_payment)
            database.session.commit()

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get(f"/paypal_checkout/resume_payment/{pending_payment.id}")

                # Should redirect to payment page
                assert response.status_code == 302
                assert f"/paypal_checkout/payment/{pending_payment.curso}" in response.location

    def test_resume_payment_invalid(self, app_with_paypal_data):
        """Test resuming a non-existent payment."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/resume_payment/999999")

                # Should redirect with error
                assert response.status_code == 302

    def test_payment_with_extreme_amounts(self, app_with_paypal_data):
        """Test payment processing with extreme amounts."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Test with very large amount
            with (
                patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
                patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
            ):

                mock_token.return_value = "mock_access_token"
                mock_verify.return_value = {
                    "verified": True,
                    "status": "COMPLETED",
                    "amount": "999.99",
                    "currency": "USD",
                    "payer_id": "test_payer_id",
                }

                with app_with_paypal_data.test_client() as client:
                    # Login as test user
                    with client.session_transaction() as sess:
                        sess["_user_id"] = user.id
                        sess["_fresh"] = True

                    response = client.post(
                        "/paypal_checkout/confirm_payment",
                        data=json.dumps(
                            {
                                "orderID": "test_order_123",
                                "payerID": "test_payer_id",
                                "courseCode": "PAYPAL002",  # Expensive course
                                "amount": 999.99,
                                "currency": "USD",
                            }
                        ),
                        content_type="application/json",
                    )

                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data["success"] is True

    def test_payment_status_with_multiple_payments(self, app_with_paypal_data):
        """Test payment status endpoint with multiple payment records."""
        from now_lms import database
        from now_lms.db import Usuario, Pago

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            # Create multiple payment records
            payment1 = Pago(
                usuario=user.usuario,
                curso="PAYPAL001",
                nombre=user.nombre,
                apellido=user.apellido,
                correo_electronico=user.correo_electronico,
                referencia="order_1",
                monto=99.99,
                moneda="USD",
                metodo="paypal",
                estado="completed",
            )
            
            payment2 = Pago(
                usuario=user.usuario,
                curso="PAYPAL001",
                nombre=user.nombre,
                apellido=user.apellido,
                correo_electronico=user.correo_electronico,
                referencia="order_2",
                monto=99.99,
                moneda="USD",
                metodo="paypal",
                estado="pending",
            )
            
            database.session.add(payment1)
            database.session.add(payment2)
            database.session.commit()

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                response = client.get("/paypal_checkout/payment_status/PAYPAL001")

                assert response.status_code == 200
                data = json.loads(response.data)
                assert len(data["payments"]) == 2
                assert data["payments"][0]["reference"] in ["order_1", "order_2"]
                assert data["payments"][1]["reference"] in ["order_1", "order_2"]


class TestPayPalSecurityAndValidation:
    """Test PayPal security features and validation."""

    def test_payment_confirmation_requires_authentication(self, app_with_paypal_data):
        """Test that payment confirmation requires user authentication."""
        with app_with_paypal_data.test_client() as client:
            # Don't login - test unauthenticated access
            response = client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(
                    {
                        "orderID": "test_order_123",
                        "payerID": "test_payer_id",
                        "courseCode": "PAYPAL001",
                        "amount": 99.99,
                        "currency": "USD",
                    }
                ),
                content_type="application/json",
            )

            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]

    def test_payment_page_requires_authentication(self, app_with_paypal_data):
        """Test that payment page requires user authentication."""
        with app_with_paypal_data.test_client() as client:
            # Don't login - test unauthenticated access
            response = client.get("/paypal_checkout/payment/PAYPAL001")

            # Should redirect to login
            assert response.status_code in [302, 401, 403]

    def test_get_client_id_requires_authentication(self, app_with_paypal_data):
        """Test that get_client_id endpoint requires authentication."""
        with app_with_paypal_data.test_client() as client:
            # Don't login - test unauthenticated access
            response = client.get("/paypal_checkout/get_client_id")

            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]

    def test_sql_injection_protection(self, app_with_paypal_data):
        """Test protection against SQL injection in payment confirmation."""
        from now_lms import database
        from now_lms.db import Usuario

        with app_with_paypal_data.app_context():
            user = database.session.execute(database.select(Usuario).filter_by(usuario="test_paypal_user")).first()[0]

            with app_with_paypal_data.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                # Attempt SQL injection in course code
                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(
                        {
                            "orderID": "test_order_123",
                            "payerID": "test_payer_id",
                            "courseCode": "PAYPAL001'; DROP TABLE usuarios; --",
                            "amount": 99.99,
                            "currency": "USD",
                        }
                    ),
                    content_type="application/json",
                )

                # Should handle safely (course not found)
                assert response.status_code in [400, 404]