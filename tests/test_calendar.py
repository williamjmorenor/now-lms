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

"""Test Calendar functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from now_lms.db import UserEvent, Usuario, database
from now_lms.vistas.calendar import _generate_ics_content, _escape_ics_text


class TestCalendarViews:
    """Test calendar views and functionality."""

    def setup_method(self):
        """Set up test data for each test."""
        # Create test user
        self.test_user = Usuario(
            usuario="testuser",
            nombre="Test",
            apellido="User",
            correo_electronico="test@example.com",
            tipo="student"
        )
        database.session.add(self.test_user)
        database.session.commit()

        # Create test events
        now = datetime.now()
        self.test_events = [
            UserEvent(
                user_id=self.test_user.usuario,
                title="Test Event 1",
                description="A test event",
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=1, hours=1),
                status="confirmed",
                timezone="UTC"
            ),
            UserEvent(
                user_id=self.test_user.usuario,
                title="Test Event 2",
                description="Another test event",
                start_time=now + timedelta(days=15),
                end_time=now + timedelta(days=15, hours=2),
                status="tentative",
                timezone="UTC"
            ),
            UserEvent(
                user_id=self.test_user.usuario,
                title="Past Event",
                description="An event in the past",
                start_time=now - timedelta(days=10),
                end_time=now - timedelta(days=10, hours=1),
                status="confirmed",
                timezone="UTC"
            )
        ]
        for event in self.test_events:
            database.session.add(event)
        database.session.commit()

    @patch('now_lms.vistas.calendar.current_user')
    def test_calendar_view_authenticated(self, mock_current_user, client, full_db_setup):
        """Test calendar view for authenticated user."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.test_user.usuario

        response = client.get('/user/calendar')
        assert response.status_code == 200
        assert b"calendar" in response.data.lower()

    @patch('now_lms.vistas.calendar.current_user')
    def test_calendar_view_with_year_month_params(self, mock_current_user, client, full_db_setup):
        """Test calendar view with specific year and month parameters."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.test_user.usuario

        response = client.get('/user/calendar?year=2024&month=12')
        assert response.status_code == 200

    def test_calendar_view_unauthenticated(self, client, full_db_setup):
        """Test calendar view redirects unauthenticated users."""
        response = client.get('/user/calendar')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.calendar.current_user')
    def test_event_detail_authenticated(self, mock_current_user, client, full_db_setup):
        """Test event detail view for authenticated user."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.test_user.usuario

        event_id = self.test_events[0].id
        response = client.get(f'/user/calendar/event/{event_id}')
        assert response.status_code == 200

    @patch('now_lms.vistas.calendar.current_user')
    def test_event_detail_not_found(self, mock_current_user, client, full_db_setup):
        """Test event detail view for non-existent event."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.test_user.usuario

        response = client.get('/user/calendar/event/999999')
        assert response.status_code == 404

    @patch('now_lms.vistas.calendar.current_user')
    def test_event_detail_unauthorized(self, mock_current_user, client, full_db_setup):
        """Test event detail view for event belonging to another user."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = "otheruser"

        event_id = self.test_events[0].id
        response = client.get(f'/user/calendar/event/{event_id}')
        assert response.status_code == 404

    def test_event_detail_unauthenticated(self, client, full_db_setup):
        """Test event detail view redirects unauthenticated users."""
        event_id = self.test_events[0].id
        response = client.get(f'/user/calendar/event/{event_id}')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.calendar.current_user')
    def test_export_ics_authenticated(self, mock_current_user, client, full_db_setup):
        """Test ICS export for authenticated user."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.test_user.usuario

        response = client.get('/user/calendar/export.ics')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/calendar; charset=utf-8'
        assert 'attachment' in response.headers['Content-Disposition']
        assert 'calendar-testuser.ics' in response.headers['Content-Disposition']

    def test_export_ics_unauthenticated(self, client, full_db_setup):
        """Test ICS export redirects unauthenticated users."""
        response = client.get('/user/calendar/export.ics')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.calendar.current_user')
    def test_upcoming_events_authenticated(self, mock_current_user, client, full_db_setup):
        """Test upcoming events view for authenticated user."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.test_user.usuario

        response = client.get('/user/calendar/upcoming')
        assert response.status_code == 200

    def test_upcoming_events_unauthenticated(self, client, full_db_setup):
        """Test upcoming events view redirects unauthenticated users."""
        response = client.get('/user/calendar/upcoming')
        assert response.status_code == 302  # Redirect to login


class TestCalendarHelpers:
    """Test calendar helper functions."""

    def test_escape_ics_text_basic(self):
        """Test basic ICS text escaping."""
        result = _escape_ics_text("Simple text")
        assert result == "Simple text"

    def test_escape_ics_text_special_chars(self):
        """Test ICS text escaping with special characters."""
        text = "Text with, comma; semicolon\nand newline"
        result = _escape_ics_text(text)
        assert result == "Text with\\, comma\\; semicolon\\nand newline"

    def test_escape_ics_text_backslash(self):
        """Test ICS text escaping with backslash."""
        text = "Text with \\ backslash"
        result = _escape_ics_text(text)
        assert result == "Text with \\\\ backslash"

    def test_escape_ics_text_empty(self):
        """Test ICS text escaping with empty string."""
        result = _escape_ics_text("")
        assert result == ""

    def test_escape_ics_text_none(self):
        """Test ICS text escaping with None."""
        result = _escape_ics_text(None)
        assert result == ""

    def test_generate_ics_content_basic(self):
        """Test basic ICS content generation."""
        # Create mock events
        now = datetime.now()
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.description = "Test Description"
        mock_event.start_time = now
        mock_event.end_time = now + timedelta(hours=1)
        mock_event.timestamp = now
        mock_event.status = "confirmed"
        mock_event.timezone = "UTC"

        events = [mock_event]
        result = _generate_ics_content(events)

        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result
        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result
        assert "SUMMARY:Test Event" in result
        assert "DESCRIPTION:Test Description" in result
        assert "STATUS:CONFIRMED" in result

    def test_generate_ics_content_tentative_status(self):
        """Test ICS content generation with tentative status."""
        now = datetime.now()
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.description = "Test Description"
        mock_event.start_time = now
        mock_event.end_time = now + timedelta(hours=1)
        mock_event.timestamp = now
        mock_event.status = "tentative"
        mock_event.timezone = "UTC"

        events = [mock_event]
        result = _generate_ics_content(events)

        assert "STATUS:TENTATIVE" in result

    def test_generate_ics_content_no_end_time(self):
        """Test ICS content generation when end_time is None."""
        now = datetime.now()
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.description = None
        mock_event.start_time = now
        mock_event.end_time = None
        mock_event.timestamp = now
        mock_event.status = "confirmed"
        mock_event.timezone = "UTC"

        events = [mock_event]
        result = _generate_ics_content(events)

        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result
        # Should set end_time to start_time + 1 hour when None
        assert "DTEND:" in result

    def test_generate_ics_content_with_timezone(self):
        """Test ICS content generation with timezone conversion (simplified)."""
        now = datetime.now()
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.description = "Test Description"
        mock_event.start_time = now
        mock_event.end_time = now + timedelta(hours=1)
        mock_event.timestamp = now
        mock_event.status = "confirmed"
        mock_event.timezone = "America/New_York"

        events = [mock_event]
        result = _generate_ics_content(events)

        # The function should handle timezone gracefully even if pytz is not available
        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result

    def test_generate_ics_content_with_invalid_timezone(self):
        """Test ICS content generation with invalid timezone (should not crash)."""
        now = datetime.now()
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.description = "Test Description"
        mock_event.start_time = now
        mock_event.end_time = now + timedelta(hours=1)
        mock_event.timestamp = now
        mock_event.status = "confirmed"
        mock_event.timezone = "Invalid/Timezone"

        events = [mock_event]
        result = _generate_ics_content(events)

        assert "BEGIN:VEVENT" in result
        assert "END:VEVENT" in result

    def test_generate_ics_content_empty_events(self):
        """Test ICS content generation with empty events list."""
        result = _generate_ics_content([])

        assert "BEGIN:VCALENDAR" in result
        assert "END:VCALENDAR" in result
        assert "BEGIN:VEVENT" not in result

    def test_generate_ics_content_special_characters_in_title(self):
        """Test ICS content generation with special characters in title."""
        now = datetime.now()
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.title = "Test, Event; with\nspecial chars"
        mock_event.description = "Test Description"
        mock_event.start_time = now
        mock_event.end_time = now + timedelta(hours=1)
        mock_event.timestamp = now
        mock_event.status = "confirmed"
        mock_event.timezone = "UTC"

        events = [mock_event]
        result = _generate_ics_content(events)

        assert "SUMMARY:Test\\, Event\\; with\\nspecial chars" in result