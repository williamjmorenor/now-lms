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

"""Test calendar utilities."""

import pytest
from datetime import datetime, date, time
from unittest.mock import patch, MagicMock

from now_lms.calendar_utils import (
    create_events_for_student_enrollment,
    update_meet_resource_events,
    update_evaluation_events,
    get_upcoming_events_for_user,
    cleanup_events_for_course_unenrollment,
    _combine_date_time,
    _get_app_timezone
)


class TestCalendarUtilities:
    """Test calendar utility functions."""

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_create_events_for_student_enrollment_with_meet_resources(self, mock_log, mock_database):
        """Test creating events for student enrollment with meet resources."""
        # Mock meet resources
        mock_resource = MagicMock()
        mock_resource.id = "resource1"
        mock_resource.nombre = "Team Meeting"
        mock_resource.descripcion = "Weekly team sync"
        mock_resource.fecha = date(2024, 12, 15)
        mock_resource.hora_inicio = time(10, 0)
        mock_resource.hora_fin = time(11, 0)
        mock_resource.seccion = "section1"
        
        # Mock database queries
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # meet resources query
                mock_result.scalars.return_value.all.return_value = [mock_resource]
                call_count[0] += 1
            elif call_count[0] == 1:  # evaluations query
                mock_result.scalars.return_value.all.return_value = []
                call_count[0] += 1
            else:  # existing event check
                mock_result.scalar_one_or_none.return_value = None
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        # Call function
        create_events_for_student_enrollment("user123", "course456")
        
        # Verify database session operations
        mock_database.session.add.assert_called()
        mock_database.session.commit.assert_called()
        mock_log.info.assert_called()

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_create_events_for_student_enrollment_with_evaluations(self, mock_log, mock_database):
        """Test creating events for student enrollment with evaluations."""
        # Mock evaluation
        mock_evaluation = MagicMock()
        mock_evaluation.id = "eval1"
        mock_evaluation.title = "Final Exam"
        mock_evaluation.description = "Course final examination"
        mock_evaluation.available_until = datetime(2024, 12, 20, 23, 59)
        mock_evaluation.section_id = "section1"
        
        # Mock database queries
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # meet resources query
                mock_result.scalars.return_value.all.return_value = []
                call_count[0] += 1
            elif call_count[0] == 1:  # evaluations query
                mock_result.scalars.return_value.all.return_value = [mock_evaluation]
                call_count[0] += 1
            else:  # existing event check
                mock_result.scalar_one_or_none.return_value = None
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        # Call function
        create_events_for_student_enrollment("user123", "course456")
        
        # Verify database session operations
        mock_database.session.add.assert_called()
        mock_database.session.commit.assert_called()
        mock_log.info.assert_called()

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_create_events_for_student_enrollment_existing_events(self, mock_log, mock_database):
        """Test creating events when events already exist."""
        # Mock existing event
        mock_existing_event = MagicMock()
        
        # Mock database queries
        call_count = [0]
        
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if call_count[0] == 0:  # meet resources query
                mock_result.scalars.return_value.all.return_value = []
                call_count[0] += 1
            elif call_count[0] == 1:  # evaluations query
                mock_result.scalars.return_value.all.return_value = []
                call_count[0] += 1
            else:  # existing event check
                mock_result.scalar_one_or_none.return_value = mock_existing_event
            return mock_result
        
        mock_database.session.execute.side_effect = mock_execute_side_effect
        
        # Call function
        create_events_for_student_enrollment("user123", "course456")
        
        # Should not add any events
        mock_database.session.add.assert_not_called()
        mock_database.session.commit.assert_called()

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_create_events_for_student_enrollment_exception(self, mock_log, mock_database):
        """Test exception handling in create_events_for_student_enrollment."""
        # Mock exception during database operation
        mock_database.session.execute.side_effect = Exception("Database error")
        
        # Call function
        create_events_for_student_enrollment("user123", "course456")
        
        # Verify error handling
        mock_log.error.assert_called()
        mock_database.session.rollback.assert_called()

    @patch('now_lms.calendar_utils.threading.Thread')
    def test_update_meet_resource_events(self, mock_thread):
        """Test updating meet resource events."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Call function
        update_meet_resource_events("resource123")
        
        # Verify thread creation and start
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    @patch('now_lms.calendar_utils.threading.Thread')
    def test_update_evaluation_events(self, mock_thread):
        """Test updating evaluation events."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Call function
        update_evaluation_events("eval123")
        
        # Verify thread creation and start
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    @patch('now_lms.calendar_utils.database')
    def test_get_upcoming_events_for_user(self, mock_database):
        """Test getting upcoming events for user."""
        # Mock events
        mock_event1 = MagicMock()
        mock_event2 = MagicMock()
        mock_events = [mock_event1, mock_event2]
        
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = mock_events
        
        # Call function
        result = get_upcoming_events_for_user("user123", limit=5)
        
        # Verify result
        assert result == mock_events
        mock_database.session.execute.assert_called()

    @patch('now_lms.calendar_utils.database')
    def test_get_upcoming_events_for_user_default_limit(self, mock_database):
        """Test getting upcoming events with default limit."""
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Call function without limit
        get_upcoming_events_for_user("user123")
        
        mock_database.session.execute.assert_called()

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_cleanup_events_for_course_unenrollment(self, mock_log, mock_database):
        """Test cleanup events for course unenrollment."""
        # Mock events to delete
        mock_event1 = MagicMock()
        mock_event2 = MagicMock()
        events_to_delete = [mock_event1, mock_event2]
        
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = events_to_delete
        
        # Call function
        cleanup_events_for_course_unenrollment("user123", "course456")
        
        # Verify deletions
        assert mock_database.session.delete.call_count == 2
        mock_database.session.commit.assert_called()
        mock_log.info.assert_called()

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_cleanup_events_for_course_unenrollment_exception(self, mock_log, mock_database):
        """Test exception handling in cleanup_events_for_course_unenrollment."""
        # Mock exception
        mock_database.session.execute.side_effect = Exception("Database error")
        
        # Call function
        cleanup_events_for_course_unenrollment("user123", "course456")
        
        # Verify error handling
        mock_log.error.assert_called()
        mock_database.session.rollback.assert_called()

    def test_combine_date_time_with_both_params(self):
        """Test _combine_date_time with both date and time."""
        test_date = date(2024, 12, 15)
        test_time = time(14, 30)
        
        result = _combine_date_time(test_date, test_time)
        
        expected = datetime(2024, 12, 15, 14, 30)
        assert result == expected

    def test_combine_date_time_with_no_time(self):
        """Test _combine_date_time with no time (uses default)."""
        test_date = date(2024, 12, 15)
        
        result = _combine_date_time(test_date, None)
        
        expected = datetime(2024, 12, 15, 9, 0)  # Default 9:00 AM
        assert result == expected

    def test_combine_date_time_with_no_date(self):
        """Test _combine_date_time with no date."""
        test_time = time(14, 30)
        
        result = _combine_date_time(None, test_time)
        
        assert result is None

    @patch('now_lms.calendar_utils.get_timezone')
    def test_get_app_timezone(self, mock_get_timezone):
        """Test _get_app_timezone function."""
        mock_get_timezone.return_value = "America/New_York"
        
        result = _get_app_timezone()
        
        assert result == "America/New_York"
        mock_get_timezone.assert_called_once()


class TestCalendarUtilitiesEdgeCases:
    """Test edge cases for calendar utilities."""

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_create_events_no_resources_or_evaluations(self, mock_log, mock_database):
        """Test creating events when no resources or evaluations exist."""
        # Mock empty results
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = []
        
        # Call function
        create_events_for_student_enrollment("user123", "course456")
        
        # Should still commit but not create any events
        mock_database.session.add.assert_not_called()
        mock_database.session.commit.assert_called()
        mock_log.info.assert_called_with("Created 0 calendar events for user user123 in course course456")

    def test_combine_date_time_edge_cases(self):
        """Test _combine_date_time with edge cases."""
        # Test with midnight
        test_date = date(2024, 1, 1)
        test_time = time(0, 0)
        
        result = _combine_date_time(test_date, test_time)
        expected = datetime(2024, 1, 1, 0, 0)
        assert result == expected
        
        # Test with end of day
        test_time = time(23, 59, 59)
        result = _combine_date_time(test_date, test_time)
        expected = datetime(2024, 1, 1, 23, 59, 59)
        assert result == expected

    @patch('now_lms.calendar_utils.database')
    def test_get_upcoming_events_empty_result(self, mock_database):
        """Test getting upcoming events when no events exist."""
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = []
        
        result = get_upcoming_events_for_user("user123")
        
        assert result == []

    @patch('now_lms.calendar_utils.database')
    @patch('now_lms.calendar_utils.log')
    def test_cleanup_events_no_events_to_delete(self, mock_log, mock_database):
        """Test cleanup when no events exist."""
        mock_database.session.execute.return_value.scalars.return_value.all.return_value = []
        
        cleanup_events_for_course_unenrollment("user123", "course456")
        
        mock_database.session.delete.assert_not_called()
        mock_database.session.commit.assert_called()
        mock_log.info.assert_called_with("Removed 0 calendar events for user user123 unenrolling from course course456")