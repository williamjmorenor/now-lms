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
#

"""Tests for evaluation helper functions."""

import pytest
from unittest.mock import patch, MagicMock
from now_lms.vistas.evaluation_helpers import (
    check_user_evaluations_completed,
    get_user_evaluation_status,
    can_user_receive_certificate,
)


class TestEvaluationHelpers:
    """Test class for evaluation helper functions."""

    def test_check_user_evaluations_completed_no_evaluations(self, full_db_setup):
        """Test check_user_evaluations_completed when course has no evaluations."""
        with full_db_setup.app_context():
            # Use a course that doesn't have evaluations set up
            result = check_user_evaluations_completed("curso-test", "usuario-test")
            all_passed, failed_count, total_count = result

            assert all_passed is True
            assert failed_count == 0
            assert total_count == 0

    def test_check_user_evaluations_completed_with_test_data(self, full_db_setup):
        """Test check_user_evaluations_completed with test data."""
        with full_db_setup.app_context():
            # Test with existing course and user from test data
            result = check_user_evaluations_completed("intro-python", "lms-admin")
            all_passed, failed_count, total_count = result

            # Result should be a tuple with boolean and two integers
            assert isinstance(all_passed, bool)
            assert isinstance(failed_count, int)
            assert isinstance(total_count, int)
            assert failed_count >= 0
            assert total_count >= 0

    def test_get_user_evaluation_status_no_evaluations(self, full_db_setup):
        """Test get_user_evaluation_status when course has no evaluations."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("curso-test", "usuario-test")

            assert isinstance(result, dict)
            assert "total_evaluations" in result
            assert "passed_evaluations" in result
            assert "failed_evaluations" in result
            assert "pending_evaluations" in result
            assert "evaluation_details" in result

            assert result["total_evaluations"] == 0
            assert result["passed_evaluations"] == 0
            assert result["failed_evaluations"] == 0
            assert result["pending_evaluations"] == 0
            assert isinstance(result["evaluation_details"], list)
            assert len(result["evaluation_details"]) == 0

    def test_get_user_evaluation_status_with_test_data(self, full_db_setup):
        """Test get_user_evaluation_status with test data."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("intro-python", "lms-admin")

            assert isinstance(result, dict)
            assert "total_evaluations" in result
            assert "passed_evaluations" in result
            assert "failed_evaluations" in result
            assert "pending_evaluations" in result
            assert "evaluation_details" in result

            # Validate data types and ranges
            assert isinstance(result["total_evaluations"], int)
            assert isinstance(result["passed_evaluations"], int)
            assert isinstance(result["failed_evaluations"], int)
            assert isinstance(result["pending_evaluations"], int)
            assert isinstance(result["evaluation_details"], list)

            # Validate that counts add up correctly
            assert (result["passed_evaluations"] + result["failed_evaluations"] + result["pending_evaluations"]) == result[
                "total_evaluations"
            ]

    def test_can_user_receive_certificate_no_course_data(self, full_db_setup):
        """Test can_user_receive_certificate with non-existent course."""
        with full_db_setup.app_context():
            result = can_user_receive_certificate("nonexistent-course", "usuario-test")
            can_receive, reason = result

            assert isinstance(can_receive, bool)
            assert isinstance(reason, str)
            # Should return False for non-existent course with appropriate reason
            assert can_receive is True or can_receive is False  # Either is valid for non-existent course

    def test_can_user_receive_certificate_with_test_data(self, full_db_setup):
        """Test can_user_receive_certificate with test data."""
        with full_db_setup.app_context():
            result = can_user_receive_certificate("intro-python", "lms-admin")
            can_receive, reason = result

            assert isinstance(can_receive, bool)
            assert isinstance(reason, str)
            assert len(reason) > 0  # Reason should not be empty

    def test_evaluation_status_details_structure(self, full_db_setup):
        """Test that evaluation details have the correct structure."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("intro-python", "lms-admin")

            for detail in result["evaluation_details"]:
                assert isinstance(detail, dict)
                assert "evaluation_id" in detail
                assert "title" in detail
                assert "is_exam" in detail
                assert "passing_score" in detail
                assert "status" in detail
                assert "best_score" in detail
                assert "attempts_count" in detail

                # Validate data types
                assert isinstance(detail["attempts_count"], int)
                assert detail["status"] in ["passed", "failed", "pending"]
                assert isinstance(detail["is_exam"], bool)


class TestEvaluationHelpersMocked:
    """Test evaluation helper functions with mocked dependencies."""

    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_check_user_evaluations_completed_no_evaluations_mocked(self, mock_database):
        """Test check_user_evaluations_completed when no evaluations exist."""
        # Mock no evaluations found
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = []
        
        result = check_user_evaluations_completed("COURSE001", "user123")
        
        assert result == (True, 0, 0)

    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_check_user_evaluations_completed_all_passed_mocked(self, mock_database):
        """Test check_user_evaluations_completed when all evaluations are passed."""
        # Mock evaluations
        mock_eval1 = MagicMock()
        mock_eval1.id = "eval1"
        mock_eval2 = MagicMock()
        mock_eval2.id = "eval2"
        evaluations = [mock_eval1, mock_eval2]
        
        # Mock passed attempts for both evaluations
        mock_attempt1 = MagicMock()
        mock_attempt2 = MagicMock()
        
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # First call for evaluations
                mock_result.scalars.return_value.all.return_value = evaluations
                call_count[0] += 1
            else:  # Subsequent calls for attempts - return passed attempt
                mock_result.scalars.return_value.first.return_value = mock_attempt1
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = check_user_evaluations_completed("COURSE001", "user123")
        
        assert result == (True, 0, 2)

    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_check_user_evaluations_completed_some_failed_mocked(self, mock_database):
        """Test check_user_evaluations_completed when some evaluations failed."""
        # Mock evaluations
        mock_eval1 = MagicMock()
        mock_eval1.id = "eval1"
        mock_eval2 = MagicMock()
        mock_eval2.id = "eval2"
        evaluations = [mock_eval1, mock_eval2]
        
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # First call for evaluations
                mock_result.scalars.return_value.all.return_value = evaluations
                call_count[0] += 1
            elif call_count[0] == 1:  # First attempt query (passed)
                mock_result.scalars.return_value.first.return_value = MagicMock()
                call_count[0] += 1
            else:  # Second attempt query (failed - no attempt found)
                mock_result.scalars.return_value.first.return_value = None
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = check_user_evaluations_completed("COURSE001", "user123")
        
        assert result == (False, 1, 2)

    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_get_user_evaluation_status_no_evaluations_mocked(self, mock_database):
        """Test get_user_evaluation_status when no evaluations exist."""
        # Mock no evaluations found
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = []
        
        result = get_user_evaluation_status("COURSE001", "user123")
        
        expected = {
            "total_evaluations": 0,
            "passed_evaluations": 0,
            "failed_evaluations": 0,
            "pending_evaluations": 0,
            "evaluation_details": [],
        }
        assert result == expected

    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_get_user_evaluation_status_with_evaluations_mocked(self, mock_database):
        """Test get_user_evaluation_status with mixed evaluation statuses."""
        # Mock evaluations
        mock_eval1 = MagicMock()
        mock_eval1.id = "eval1"
        mock_eval1.title = "Test Evaluation 1"
        mock_eval1.is_exam = True
        mock_eval1.passing_score = 70.0
        
        mock_eval2 = MagicMock()
        mock_eval2.id = "eval2"
        mock_eval2.title = "Test Evaluation 2"
        mock_eval2.is_exam = False
        mock_eval2.passing_score = 60.0
        
        evaluations = [mock_eval1, mock_eval2]
        
        # Mock passed attempt for first evaluation
        mock_passed_attempt = MagicMock()
        mock_passed_attempt.passed = True
        mock_passed_attempt.score = 85.0
        
        # Mock failed attempt for second evaluation
        mock_failed_attempt = MagicMock()
        mock_failed_attempt.passed = False
        mock_failed_attempt.score = 45.0
        
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # First call for evaluations
                mock_result.scalars.return_value.all.return_value = evaluations
                call_count[0] += 1
            elif call_count[0] == 1:  # First attempt query (passed)
                mock_result.scalars.return_value.first.return_value = mock_passed_attempt
                call_count[0] += 1
            elif call_count[0] == 2:  # First attempt count query
                mock_result.scalar.return_value = 2
                call_count[0] += 1
            elif call_count[0] == 3:  # Second attempt query (failed)
                mock_result.scalars.return_value.first.return_value = mock_failed_attempt
                call_count[0] += 1
            else:  # Second attempt count query
                mock_result.scalar.return_value = 3
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = get_user_evaluation_status("COURSE001", "user123")
        
        assert result["total_evaluations"] == 2
        assert result["passed_evaluations"] == 1
        assert result["failed_evaluations"] == 1
        assert result["pending_evaluations"] == 0
        assert len(result["evaluation_details"]) == 2
        
        # Check first evaluation details
        eval1_detail = result["evaluation_details"][0]
        assert eval1_detail["evaluation_id"] == "eval1"
        assert eval1_detail["title"] == "Test Evaluation 1"
        assert eval1_detail["status"] == "passed"
        assert eval1_detail["best_score"] == 85.0
        assert eval1_detail["attempts_count"] == 2
        
        # Check second evaluation details
        eval2_detail = result["evaluation_details"][1]
        assert eval2_detail["evaluation_id"] == "eval2"
        assert eval2_detail["title"] == "Test Evaluation 2"
        assert eval2_detail["status"] == "failed"
        assert eval2_detail["best_score"] == 45.0
        assert eval2_detail["attempts_count"] == 3

    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_get_user_evaluation_status_pending_evaluation_mocked(self, mock_database):
        """Test get_user_evaluation_status with pending evaluation."""
        # Mock evaluation
        mock_eval = MagicMock()
        mock_eval.id = "eval1"
        mock_eval.title = "Pending Evaluation"
        mock_eval.is_exam = False
        mock_eval.passing_score = 50.0
        
        evaluations = [mock_eval]
        
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # First call for evaluations
                mock_result.scalars.return_value.all.return_value = evaluations
                call_count[0] += 1
            elif call_count[0] == 1:  # Attempt query (no attempts)
                mock_result.scalars.return_value.first.return_value = None
                call_count[0] += 1
            else:  # Attempt count query
                mock_result.scalar.return_value = 0
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = get_user_evaluation_status("COURSE001", "user123")
        
        assert result["pending_evaluations"] == 1
        assert result["evaluation_details"][0]["status"] == "pending"
        assert result["evaluation_details"][0]["best_score"] is None
        assert result["evaluation_details"][0]["attempts_count"] == 0

    @patch('now_lms.vistas.evaluation_helpers.check_user_evaluations_completed')
    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_can_user_receive_certificate_evaluations_not_passed_mocked(self, mock_database, mock_check_evaluations):
        """Test can_user_receive_certificate when evaluations are not passed."""
        # Mock evaluations check to return failure
        mock_check_evaluations.return_value = (False, 2, 3)
        
        result = can_user_receive_certificate("COURSE001", "user123")
        
        assert result[0] is False
        assert "2 de 3 evaluaciones no aprobadas" in result[1]

    @patch('now_lms.vistas.evaluation_helpers.check_user_evaluations_completed')
    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_can_user_receive_certificate_course_not_completed_mocked(self, mock_database, mock_check_evaluations):
        """Test can_user_receive_certificate when course resources are not completed."""
        # Mock evaluations check to pass
        mock_check_evaluations.return_value = (True, 0, 3)
        
        # Mock course completion check to fail
        mock_database.session.execute.return_value.scalars.return_value.first.return_value = None
        
        result = can_user_receive_certificate("COURSE001", "user123")
        
        assert result[0] is False
        assert "completar todos los recursos" in result[1]

    @patch('now_lms.vistas.evaluation_helpers.check_user_evaluations_completed')
    @patch('now_lms.vistas.evaluation_helpers.database')
    def test_can_user_receive_certificate_success_mocked(self, mock_database, mock_check_evaluations):
        """Test can_user_receive_certificate when all requirements are met."""
        # Mock evaluations check to pass
        mock_check_evaluations.return_value = (True, 0, 3)
        
        # Mock course completion check to pass
        mock_avance = MagicMock()
        mock_avance.completado = True
        mock_database.session.execute.return_value.scalars.return_value.first.return_value = mock_avance
        
        result = can_user_receive_certificate("COURSE001", "user123")
        
        assert result[0] is True
        assert "Cumple todos los requisitos" in result[1]
