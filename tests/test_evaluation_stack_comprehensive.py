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

"""Comprehensive tests for Evaluation Stack - Complete test coverage."""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from now_lms.db import (
    Evaluation,
    Question,
    QuestionOption,
    EvaluationAttempt,
    Answer,
    EvaluationReopenRequest,
    Curso,
    CursoSeccion,
    EstudianteCurso,
    Usuario,
    Certificado,
    database,
)
from now_lms.vistas.evaluations import (
    can_user_access_evaluation,
    is_evaluation_available,
    get_user_attempts_count,
    can_user_attempt_evaluation,
    calculate_score,
)
from now_lms.vistas.evaluation_helpers import (
    check_user_evaluations_completed,
    get_user_evaluation_status,
    can_user_receive_certificate,
)


class TestEvaluationModels:
    """Test evaluation model creation and basic functionality."""

    def test_evaluation_model_creation(self, app_context):
        """Test basic Evaluation model creation."""
        eval_obj = Evaluation(
            section_id="test_section_001",
            title="Python Fundamentals Quiz",
            description="A comprehensive quiz covering Python basics",
            is_exam=False,
            passing_score=75.0,
            max_attempts=3,
            available_until=datetime.now() + timedelta(days=7),
            penalty_percent=10.0
        )
        
        assert eval_obj.title == "Python Fundamentals Quiz"
        assert eval_obj.description == "A comprehensive quiz covering Python basics"
        assert eval_obj.is_exam is False
        assert eval_obj.passing_score == 75.0
        assert eval_obj.max_attempts == 3
        assert eval_obj.penalty_percent == 10.0
        assert eval_obj.available_until is not None

    def test_evaluation_exam_type(self, app_context):
        """Test exam-type evaluation creation."""
        exam = Evaluation(
            section_id="test_section_002",
            title="Final Python Certification Exam",
            description="Comprehensive final exam for certification",
            is_exam=True,
            passing_score=85.0,
            max_attempts=1
        )
        
        assert exam.is_exam is True
        assert exam.passing_score == 85.0
        assert exam.max_attempts == 1

    def test_question_model_creation(self, app_context):
        """Test Question model creation."""
        multiple_question = Question(
            evaluation_id="eval_001",
            type="multiple",
            text="Which of the following are Python data types?",
            explanation="Python has several built-in data types.",
            order=1
        )
        
        assert multiple_question.type == "multiple"
        assert multiple_question.text == "Which of the following are Python data types?"
        assert multiple_question.explanation is not None
        assert multiple_question.order == 1

    def test_boolean_question_creation(self, app_context):
        """Test boolean question creation."""
        boolean_question = Question(
            evaluation_id="eval_001",
            type="boolean",
            text="Python is an interpreted language.",
            explanation="Python code is executed line by line.",
            order=2
        )
        
        assert boolean_question.type == "boolean"
        assert boolean_question.text == "Python is an interpreted language."

    def test_question_option_creation(self, app_context):
        """Test QuestionOption model creation."""
        correct_option = QuestionOption(
            question_id="question_001",
            text="List",
            is_correct=True
        )
        
        incorrect_option = QuestionOption(
            question_id="question_001",
            text="Database",
            is_correct=False
        )
        
        assert correct_option.text == "List"
        assert correct_option.is_correct is True
        assert incorrect_option.text == "Database"
        assert incorrect_option.is_correct is False

    def test_evaluation_attempt_creation(self, app_context):
        """Test EvaluationAttempt model creation."""
        attempt = EvaluationAttempt(
            evaluation_id="eval_001",
            user_id="student_001",
            score=87.5,
            passed=True,
            started_at=datetime.now(),
            submitted_at=datetime.now() + timedelta(minutes=30),
            was_late=False
        )
        
        assert attempt.evaluation_id == "eval_001"
        assert attempt.user_id == "student_001"
        assert attempt.score == 87.5
        assert attempt.passed is True
        assert attempt.was_late is False

    def test_answer_model_creation(self, app_context):
        """Test Answer model creation."""
        answer = Answer(
            attempt_id="attempt_001",
            question_id="question_001",
            selected_option_ids='["option_001", "option_003"]'
        )
        
        assert answer.attempt_id == "attempt_001"
        assert answer.question_id == "question_001"
        
        # Test JSON parsing
        selected_ids = json.loads(answer.selected_option_ids)
        assert len(selected_ids) == 2
        assert "option_001" in selected_ids

    def test_reopen_request_creation(self, app_context):
        """Test EvaluationReopenRequest model creation."""
        reopen_request = EvaluationReopenRequest(
            user_id="student_001",
            evaluation_id="eval_001",
            justification_text="Technical difficulties during last attempt.",
            status="pending"
        )
        
        assert reopen_request.user_id == "student_001"
        assert reopen_request.evaluation_id == "eval_001"
        assert "Technical difficulties" in reopen_request.justification_text
        assert reopen_request.status == "pending"


class TestEvaluationBusinessLogic:
    """Test evaluation business logic functions."""

    def test_evaluation_availability_with_deadline(self, app_context):
        """Test evaluation availability checking."""
        # Available evaluation
        available_eval = Evaluation(
            section_id="test_section",
            title="Available Quiz",
            available_until=datetime.now() + timedelta(hours=2)
        )
        
        assert is_evaluation_available(available_eval) is True
        
        # Expired evaluation
        expired_eval = Evaluation(
            section_id="test_section",
            title="Expired Quiz",
            available_until=datetime.now() - timedelta(hours=1)
        )
        
        assert is_evaluation_available(expired_eval) is False

    def test_evaluation_availability_no_deadline(self, app_context):
        """Test evaluation availability without deadline."""
        no_deadline_eval = Evaluation(
            section_id="test_section",
            title="Always Available Quiz",
            available_until=None
        )
        
        assert is_evaluation_available(no_deadline_eval) is True

    @patch('now_lms.vistas.evaluations.database')
    def test_get_user_attempts_count(self, mock_database):
        """Test getting user attempt count."""
        mock_database.session.execute.return_value.scalar.return_value = 2
        
        count = get_user_attempts_count("eval_001", "user_001")
        
        assert count == 2
        mock_database.session.execute.assert_called_once()

    @patch('now_lms.vistas.evaluations.can_user_access_evaluation')
    @patch('now_lms.vistas.evaluations.is_evaluation_available')
    @patch('now_lms.vistas.evaluations.get_user_attempts_count')
    def test_can_user_attempt_evaluation_success(self, mock_attempts, mock_available, mock_access):
        """Test successful evaluation attempt permission."""
        mock_access.return_value = True
        mock_available.return_value = True
        mock_attempts.return_value = 1
        
        evaluation = MagicMock()
        evaluation.max_attempts = 3
        user = MagicMock()
        
        result = can_user_attempt_evaluation(evaluation, user)
        
        assert result is True
        mock_access.assert_called_once_with(evaluation, user)
        mock_available.assert_called_once_with(evaluation)

    @patch('now_lms.vistas.evaluations.can_user_access_evaluation')
    @patch('now_lms.vistas.evaluations.is_evaluation_available')
    @patch('now_lms.vistas.evaluations.get_user_attempts_count')
    def test_can_user_attempt_evaluation_max_attempts_reached(self, mock_attempts, mock_available, mock_access):
        """Test evaluation attempt when max attempts reached."""
        mock_access.return_value = True
        mock_available.return_value = True
        mock_attempts.return_value = 3
        
        evaluation = MagicMock()
        evaluation.max_attempts = 3
        user = MagicMock()
        
        result = can_user_attempt_evaluation(evaluation, user)
        
        assert result is False

    @patch('now_lms.vistas.evaluations.can_user_access_evaluation')
    def test_can_user_attempt_evaluation_no_access(self, mock_access):
        """Test evaluation attempt when user has no access."""
        mock_access.return_value = False
        
        evaluation = MagicMock()
        user = MagicMock()
        
        result = can_user_attempt_evaluation(evaluation, user)
        
        assert result is False


class TestEvaluationScoring:
    """Test evaluation scoring system."""

    def test_calculate_score_boolean_questions(self, app_context):
        """Test score calculation for boolean questions."""
        evaluation = MagicMock()
        question = MagicMock()
        question.type = "boolean"
        
        correct_option = MagicMock()
        correct_option.is_correct = True
        
        answer = MagicMock()
        answer.selected_option_ids = '["option_001"]'
        answer.question = question
        
        attempt = MagicMock()
        attempt.evaluation = evaluation
        attempt.answers = [answer]
        evaluation.questions = [question]
        
        with patch('now_lms.vistas.evaluations.database') as mock_db:
            mock_db.session.get.return_value = correct_option
            score = calculate_score(attempt)
            assert score == 100.0

    def test_calculate_score_multiple_choice_questions(self, app_context):
        """Test score calculation for multiple choice questions."""
        evaluation = MagicMock()
        question = MagicMock()
        question.type = "multiple"
        
        correct_option1 = MagicMock()
        correct_option1.id = "opt_001"
        correct_option1.is_correct = True
        
        correct_option2 = MagicMock()
        correct_option2.id = "opt_002"
        correct_option2.is_correct = True
        
        question.options = [correct_option1, correct_option2]
        
        answer = MagicMock()
        answer.selected_option_ids = '["opt_001", "opt_002"]'
        answer.question = question
        
        attempt = MagicMock()
        attempt.evaluation = evaluation
        attempt.answers = [answer]
        evaluation.questions = [question]
        
        score = calculate_score(attempt)
        assert score == 100.0

    def test_calculate_score_no_questions(self, app_context):
        """Test score calculation when evaluation has no questions."""
        evaluation = MagicMock()
        evaluation.questions = []
        
        attempt = MagicMock()
        attempt.evaluation = evaluation
        attempt.answers = []
        
        score = calculate_score(attempt)
        assert score == 0.0

    def test_calculate_score_mixed_results(self, app_context):
        """Test score calculation with mixed correct/incorrect answers."""
        evaluation = MagicMock()
        
        # Correct boolean question
        bool_question = MagicMock()
        bool_question.type = "boolean"
        bool_answer = MagicMock()
        bool_answer.selected_option_ids = '["bool_opt_001"]'
        bool_answer.question = bool_question
        
        # Incorrect multiple choice question
        multi_question = MagicMock()
        multi_question.type = "multiple"
        correct_option = MagicMock()
        correct_option.id = "multi_opt_001"
        correct_option.is_correct = True
        multi_question.options = [correct_option]
        
        multi_answer = MagicMock()
        multi_answer.selected_option_ids = '["multi_opt_002"]'  # Wrong option
        multi_answer.question = multi_question
        
        attempt = MagicMock()
        attempt.evaluation = evaluation
        attempt.answers = [bool_answer, multi_answer]
        evaluation.questions = [bool_question, multi_question]
        
        with patch('now_lms.vistas.evaluations.database') as mock_db:
            bool_correct_option = MagicMock()
            bool_correct_option.is_correct = True
            mock_db.session.get.return_value = bool_correct_option
            
            score = calculate_score(attempt)
            assert score == 50.0  # 1 out of 2 questions correct


class TestEvaluationAccessControl:
    """Test evaluation access control."""

    @patch('now_lms.vistas.evaluations.database')
    def test_can_user_access_evaluation_free_course(self, mock_database):
        """Test access for enrolled user in free course."""
        section = MagicMock()
        section.curso = "COURSE001"
        
        course = MagicMock()
        course.pagado = False
        
        enrollment = MagicMock()
        
        evaluation = MagicMock()
        evaluation.section_id = "section_001"
        
        user = MagicMock()
        user.usuario = "user_001"
        
        def mock_session_get(model, id_value):
            if model.__name__ == "CursoSeccion":
                return section
            return None
        
        def mock_execute_side_effect(query):
            mock_result = MagicMock()
            if "EstudianteCurso" in str(query):
                mock_result.scalars.return_value.first.return_value = enrollment
            elif "Curso" in str(query):
                mock_result.scalars.return_value.first.return_value = course
            return mock_result
        
        mock_database.session.get.side_effect = mock_session_get
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = can_user_access_evaluation(evaluation, user)
        assert result is True

    @patch('now_lms.vistas.evaluations.database')
    def test_can_user_access_evaluation_paid_course_with_payment(self, mock_database):
        """Test access for user in paid course with payment."""
        section = MagicMock()
        section.curso = "PAID_COURSE001"
        
        course = MagicMock()
        course.pagado = True
        
        enrollment = MagicMock()
        enrollment.pago = True
        
        evaluation = MagicMock()
        evaluation.section_id = "section_001"
        
        user = MagicMock()
        user.usuario = "user_001"
        
        def mock_session_get(model, id_value):
            if model.__name__ == "CursoSeccion":
                return section
            return None
        
        def mock_execute_side_effect(query):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = enrollment
            return mock_result
        
        mock_database.session.get.side_effect = mock_session_get
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = can_user_access_evaluation(evaluation, user)
        assert result is True

    @patch('now_lms.vistas.evaluations.database')
    def test_can_user_access_evaluation_paid_course_no_payment(self, mock_database):
        """Test access denial for user in paid course without payment."""
        section = MagicMock()
        section.curso = "PAID_COURSE001"
        
        course = MagicMock()
        course.pagado = True
        
        enrollment = MagicMock()
        enrollment.pago = False
        
        evaluation = MagicMock()
        evaluation.section_id = "section_001"
        
        user = MagicMock()
        user.usuario = "user_001"
        
        def mock_session_get(model, id_value):
            if model.__name__ == "CursoSeccion":
                return section
            return None
        
        def mock_execute_side_effect(query):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = enrollment
            return mock_result
        
        mock_database.session.get.side_effect = mock_session_get
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = can_user_access_evaluation(evaluation, user)
        assert result is False

    @patch('now_lms.vistas.evaluations.database')
    def test_can_user_access_evaluation_not_enrolled(self, mock_database):
        """Test access denial for non-enrolled user."""
        section = MagicMock()
        section.curso = "COURSE001"
        
        evaluation = MagicMock()
        evaluation.section_id = "section_001"
        
        user = MagicMock()
        user.usuario = "user_001"
        
        def mock_session_get(model, id_value):
            if model.__name__ == "CursoSeccion":
                return section
            return None
        
        def mock_execute_side_effect(query):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None  # No enrollment
            return mock_result
        
        mock_database.session.get.side_effect = mock_session_get
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        result = can_user_access_evaluation(evaluation, user)
        assert result is False


class TestEvaluationDatabaseIntegration:
    """Test evaluation database integration."""

    def test_evaluation_creation_in_database(self, full_db_setup):
        """Test creating and persisting evaluation in database."""
        with full_db_setup.app_context():
            # Create a course and section first
            course = Curso(
                codigo="EVAL_TEST_001",
                nombre="Evaluation Test Course",
                descripcion_corta="Course for testing evaluations",
                descripcion="A course specifically for testing evaluation functionality",
                estado="open",
                modalidad="time_based",
                pagado=False,
                certificado=True
            )
            
            database.session.add(course)
            database.session.commit()
            
            section = CursoSeccion(
                curso=course.codigo,
                nombre="Unit 1: Basics",
                descripcion="Basic concepts section",
                indice=1,
                estado=True
            )
            
            database.session.add(section)
            database.session.commit()
            
            # Create evaluation
            evaluation = Evaluation(
                section_id=section.id,
                title="Unit 1 Quiz",
                description="Quiz covering basic concepts",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3
            )
            
            database.session.add(evaluation)
            database.session.commit()
            
            # Verify persistence
            retrieved_eval = database.session.get(Evaluation, evaluation.id)
            assert retrieved_eval.title == "Unit 1 Quiz"
            assert retrieved_eval.passing_score == 70.0
            assert retrieved_eval.max_attempts == 3
            assert retrieved_eval.section_id == section.id

    def test_question_and_options_in_database(self, full_db_setup):
        """Test creating questions and options in database."""
        with full_db_setup.app_context():
            # Create evaluation first (using existing test data structure)
            evaluation = Evaluation(
                section_id="test_section_db",
                title="Database Test Quiz",
                description="Testing question creation",
                passing_score=75.0
            )
            
            database.session.add(evaluation)
            database.session.commit()
            
            # Create question
            question = Question(
                evaluation_id=evaluation.id,
                type="multiple",
                text="Which are programming languages?",
                explanation="Multiple programming languages exist.",
                order=1
            )
            
            database.session.add(question)
            database.session.commit()
            
            # Create options
            options = [
                QuestionOption(question_id=question.id, text="Python", is_correct=True),
                QuestionOption(question_id=question.id, text="Java", is_correct=True),
                QuestionOption(question_id=question.id, text="HTML", is_correct=False),
                QuestionOption(question_id=question.id, text="CSS", is_correct=False)
            ]
            
            for option in options:
                database.session.add(option)
            database.session.commit()
            
            # Verify persistence
            retrieved_question = database.session.get(Question, question.id)
            assert retrieved_question.text == "Which are programming languages?"
            assert retrieved_question.type == "multiple"
            
            # Check options
            retrieved_options = database.session.execute(
                database.select(QuestionOption).filter_by(question_id=question.id)
            ).scalars().all()
            
            assert len(retrieved_options) == 4
            correct_options = [opt for opt in retrieved_options if opt.is_correct]
            assert len(correct_options) == 2

    def test_evaluation_attempt_in_database(self, full_db_setup):
        """Test creating evaluation attempt in database."""
        with full_db_setup.app_context():
            # Create evaluation
            evaluation = Evaluation(
                section_id="test_section_attempt",
                title="Attempt Test Quiz",
                description="Testing attempt creation",
                passing_score=80.0
            )
            
            database.session.add(evaluation)
            database.session.commit()
            
            # Create attempt
            attempt = EvaluationAttempt(
                evaluation_id=evaluation.id,
                user_id="test_user_001",
                score=85.0,
                passed=True,
                started_at=datetime.now(),
                submitted_at=datetime.now() + timedelta(minutes=20),
                was_late=False
            )
            
            database.session.add(attempt)
            database.session.commit()
            
            # Verify persistence
            retrieved_attempt = database.session.get(EvaluationAttempt, attempt.id)
            assert retrieved_attempt.score == 85.0
            assert retrieved_attempt.passed is True
            assert retrieved_attempt.was_late is False
            assert retrieved_attempt.user_id == "test_user_001"


class TestEvaluationHelperFunctions:
    """Test evaluation helper functions with real database."""

    def test_check_user_evaluations_completed_with_existing_data(self, full_db_setup):
        """Test evaluation completion checking with existing data."""
        with full_db_setup.app_context():
            # Test with existing course
            all_passed, failed_count, total_count = check_user_evaluations_completed("intro-python", "lms-admin")
            
            assert isinstance(all_passed, bool)
            assert isinstance(failed_count, int)
            assert isinstance(total_count, int)
            assert failed_count >= 0
            assert total_count >= 0
            assert failed_count <= total_count

    def test_get_user_evaluation_status_with_existing_data(self, full_db_setup):
        """Test evaluation status with existing data."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("intro-python", "lms-admin")
            
            assert isinstance(result, dict)
            assert "total_evaluations" in result
            assert "passed_evaluations" in result
            assert "failed_evaluations" in result
            assert "pending_evaluations" in result
            assert "evaluation_details" in result
            
            # Verify counts add up
            total = result["total_evaluations"]
            passed = result["passed_evaluations"]
            failed = result["failed_evaluations"] 
            pending = result["pending_evaluations"]
            
            assert (passed + failed + pending) == total

    def test_can_user_receive_certificate_with_existing_data(self, full_db_setup):
        """Test certificate eligibility with existing data."""
        with full_db_setup.app_context():
            can_receive, reason = can_user_receive_certificate("intro-python", "lms-admin")
            
            assert isinstance(can_receive, bool)
            assert isinstance(reason, str)
            assert len(reason) > 0

    def test_evaluation_status_details_structure(self, full_db_setup):
        """Test evaluation status details structure."""
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


class TestEvaluationReopenRequests:
    """Test evaluation reopen request functionality."""

    def test_reopen_request_creation_in_database(self, full_db_setup):
        """Test creating reopen request in database."""
        with full_db_setup.app_context():
            # Create evaluation first
            evaluation = Evaluation(
                section_id="test_section_reopen",
                title="Reopen Test Quiz",
                description="Testing reopen requests",
                passing_score=80.0,
                max_attempts=2
            )
            
            database.session.add(evaluation)
            database.session.commit()
            
            # Create reopen request
            reopen_request = EvaluationReopenRequest(
                user_id="test_user_002",
                evaluation_id=evaluation.id,
                justification_text="I experienced technical difficulties during my attempts.",
                status="pending"
            )
            
            database.session.add(reopen_request)
            database.session.commit()
            
            # Verify persistence
            retrieved_request = database.session.get(EvaluationReopenRequest, reopen_request.id)
            assert retrieved_request.user_id == "test_user_002"
            assert retrieved_request.evaluation_id == evaluation.id
            assert "technical difficulties" in retrieved_request.justification_text
            assert retrieved_request.status == "pending"

    def test_reopen_request_status_transitions(self, full_db_setup):
        """Test reopen request status changes."""
        with full_db_setup.app_context():
            # Create evaluation
            evaluation = Evaluation(
                section_id="test_section_status",
                title="Status Test Quiz",
                description="Testing status transitions",
                passing_score=75.0
            )
            
            database.session.add(evaluation)
            database.session.commit()
            
            # Create request
            request = EvaluationReopenRequest(
                user_id="test_user_003",
                evaluation_id=evaluation.id,
                justification_text="Need another chance.",
                status="pending"
            )
            
            database.session.add(request)
            database.session.commit()
            
            # Approve request
            request.status = "approved"
            request.reviewed_at = datetime.now()
            request.approved_by = "instructor_001"
            database.session.commit()
            
            # Verify changes
            retrieved_request = database.session.get(EvaluationReopenRequest, request.id)
            assert retrieved_request.status == "approved"
            assert retrieved_request.reviewed_at is not None
            assert retrieved_request.approved_by == "instructor_001"


class TestEvaluationAdvancedFeatures:
    """Test advanced evaluation features."""

    def test_evaluation_with_penalty_system(self, app_context):
        """Test evaluation with penalty scoring."""
        evaluation = Evaluation(
            section_id="test_section",
            title="Timed Quiz with Penalties",
            description="Quiz with time penalties",
            passing_score=80.0,
            max_attempts=2,
            penalty_percent=15.0
        )
        
        assert evaluation.penalty_percent == 15.0

    def test_evaluation_unlimited_attempts(self, app_context):
        """Test evaluation with unlimited attempts."""
        evaluation = Evaluation(
            section_id="test_section",
            title="Practice Quiz",
            description="Practice quiz with unlimited attempts",
            passing_score=60.0,
            max_attempts=None
        )
        
        assert evaluation.max_attempts is None

    def test_evaluation_with_reopening_system(self, app_context):
        """Test evaluation reopening functionality."""
        evaluation = Evaluation(
            section_id="test_section",
            title="Final Exam",
            description="Final certification exam",
            passing_score=85.0,
            max_attempts=1,
            reopened_at=datetime.now(),
            reopened_for_user_id="student_001"
        )
        
        assert evaluation.reopened_at is not None
        assert evaluation.reopened_for_user_id == "student_001"

    def test_complex_multiple_choice_question(self, app_context):
        """Test complex multiple choice questions."""
        question = Question(
            evaluation_id="eval_001",
            type="multiple",
            text="Select all Python web frameworks:",
            explanation="Python has several popular web frameworks.",
            order=1
        )
        
        # Multiple correct options
        options = [
            QuestionOption(question_id=question.id, text="Django", is_correct=True),
            QuestionOption(question_id=question.id, text="Flask", is_correct=True),
            QuestionOption(question_id=question.id, text="FastAPI", is_correct=True),
            QuestionOption(question_id=question.id, text="React", is_correct=False)
        ]
        
        question.options = options
        correct_count = sum(1 for opt in options if opt.is_correct)
        assert correct_count == 3

    def test_evaluation_attempt_timing(self, app_context):
        """Test evaluation attempt timing tracking."""
        start_time = datetime.now()
        submit_time = start_time + timedelta(minutes=45)
        
        attempt = EvaluationAttempt(
            evaluation_id="eval_001",
            user_id="student_001",
            started_at=start_time,
            submitted_at=submit_time,
            was_late=False
        )
        
        # Calculate duration
        duration = attempt.submitted_at - attempt.started_at
        assert duration.total_seconds() == 45 * 60  # 45 minutes

    def test_evaluation_late_submission(self, app_context):
        """Test late evaluation submission tracking."""
        attempt = EvaluationAttempt(
            evaluation_id="eval_001",
            user_id="student_001",
            started_at=datetime.now() - timedelta(hours=2),
            submitted_at=datetime.now(),
            was_late=True,
            score=75.0,
            passed=True
        )
        
        assert attempt.was_late is True
        assert attempt.score == 75.0
        assert attempt.passed is True


class TestEvaluationEdgeCases:
    """Test evaluation system edge cases and error handling."""

    def test_evaluation_with_invalid_data(self, app_context):
        """Test evaluation creation with edge case data."""
        # Very high passing score
        high_score_eval = Evaluation(
            section_id="test_section",
            title="Impossible Quiz",
            passing_score=150.0  # Over 100%
        )
        
        assert high_score_eval.passing_score == 150.0
        
        # Zero max attempts
        zero_attempts_eval = Evaluation(
            section_id="test_section",
            title="No Attempts Quiz",
            passing_score=70.0,
            max_attempts=0
        )
        
        assert zero_attempts_eval.max_attempts == 0

    def test_evaluation_attempt_without_submission(self, app_context):
        """Test evaluation attempt without submission."""
        attempt = EvaluationAttempt(
            evaluation_id="eval_001",
            user_id="student_001",
            started_at=datetime.now(),
            submitted_at=None,
            score=None,
            passed=None
        )
        
        assert attempt.submitted_at is None
        assert attempt.score is None
        assert attempt.passed is None

    def test_answer_with_invalid_json(self, app_context):
        """Test answer with malformed JSON."""
        answer = Answer(
            attempt_id="attempt_001",
            question_id="question_001",
            selected_option_ids='invalid json'
        )
        
        assert answer.selected_option_ids == 'invalid json'
        
        # Test JSON parsing error handling
        try:
            json.loads(answer.selected_option_ids)
            assert False, "Should have raised JSON decode error"
        except json.JSONDecodeError:
            assert True

    def test_reopen_request_with_long_justification(self, app_context):
        """Test reopen request with very long justification."""
        long_text = "A" * 1500  # Very long justification
        
        request = EvaluationReopenRequest(
            user_id="student_001",
            evaluation_id="eval_001",
            justification_text=long_text,
            status="pending"
        )
        
        assert len(request.justification_text) == 1500

    def test_evaluation_past_deadline_availability(self, app_context):
        """Test evaluation availability past deadline."""
        past_deadline = datetime.now() - timedelta(days=5)
        
        evaluation = Evaluation(
            section_id="test_section",
            title="Expired Evaluation",
            available_until=past_deadline
        )
        
        assert is_evaluation_available(evaluation) is False

    def test_question_without_explanation(self, app_context):
        """Test question creation without explanation."""
        question = Question(
            evaluation_id="eval_001",
            type="boolean",
            text="Python is interpreted.",
            explanation=None,
            order=1
        )
        
        assert question.explanation is None
        assert question.text == "Python is interpreted."