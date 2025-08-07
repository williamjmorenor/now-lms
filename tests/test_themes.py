# Copyright 2021 -2023 William José Moreno Reyes
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

import pytest


"""
Casos de uso mas comunes.
"""


@pytest.fixture
def lms_application():
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "jgjañlsldaksjdklasjfkjj",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_ECHO": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app



def test_theme_functionality_comprehensive(full_db_setup):
    """Test comprehensive theme functionality including overrides and custom pages."""
    lms_application = full_db_setup

    from now_lms import database
    from now_lms.themes import (
        get_home_template,
        get_course_list_template,
        get_program_list_template,
        get_course_view_template,
        get_program_view_template,
    )

    with lms_application.app_context():
        with lms_application.test_client() as client:
            client.get("/user/logout")
            
        # Test default template returns
        assert get_home_template() == "inicio/home.html"
        assert get_course_list_template() == "inicio/cursos.html"
        assert get_program_list_template() == "inicio/programas.html"
        assert get_course_view_template() == "learning/curso/curso.html"
        assert get_program_view_template() == "learning/programa.html"

        # Test theme configuration change
        from now_lms.db import Style

        config = database.session.execute(database.select(Style)).first()[0]
        original_theme = config.theme

        # Change to Harvard theme
        config.theme = "harvard"
        database.session.commit()

        # Test template override detection
        expected_harvard_home = "themes/harvard/overrides/home.j2"

        assert get_home_template() == expected_harvard_home

        # Test Cambridge theme
        config.theme = "cambridge"
        database.session.commit()

        assert get_home_template() == "themes/cambridge/overrides/home.j2"

        # Test Oxford theme
        config.theme = "oxford"
        database.session.commit()

        assert get_home_template() == "themes/oxford/overrides/home.j2"

        # Test all other themes have override templates
        themes_to_test = ["classic", "corporative", "finance", "oxford", "cambridge", "harvard"]

        for theme in themes_to_test:
            config.theme = theme
            database.session.commit()

            # All themes should have override templates
            assert get_home_template() == f"themes/{theme}/overrides/home.j2"

        # Restore original theme
        config.theme = original_theme
        database.session.commit()

    with lms_application.test_client() as client:
        # Test custom pages functionality

        # Test valid custom page access with Harvard theme
        with lms_application.app_context():
            config = database.session.execute(database.select(Style)).first()[0]
            config.theme = "harvard"
            database.session.commit()

        # Test invalid page name security
        invalid_page_response = client.get("/custom/../../etc/passwd")
        assert invalid_page_response.status_code == 404

        # Test invalid characters in page name
        invalid_chars_response = client.get("/custom/test$page")
        assert invalid_chars_response.status_code == 302

        # Test non-existent custom page
        nonexistent_response = client.get("/custom/nonexistent")
        assert nonexistent_response.status_code == 302

        # Test theme access to home page with override
        home_response = client.get("/")
        assert home_response.status_code == 200
        assert "Harvard Academic LMS" in home_response.data.decode("utf-8")

        # Test course listing with theme override
        course_list_response = client.get("/course/explore")
        assert course_list_response.status_code == 200

        # Test program listing with theme override
        program_list_response = client.get("/program/explore")
        assert program_list_response.status_code == 200

        # Test CSS file loading for Harvard theme
        css_response = client.get("/static/themes/harvard/theme.min.css")
        assert css_response.status_code == 200
        assert "harvard-primary" in css_response.data.decode("utf-8")

        # Test other academic theme CSS files
        cambridge_css = client.get("/static/themes/cambridge/theme.min.css")
        assert cambridge_css.status_code == 200
        assert "cambridge-primary" in cambridge_css.data.decode("utf-8")

        oxford_css = client.get("/static/themes/oxford/theme.min.css")
        assert oxford_css.status_code == 200

        # Test cache invalidation works with theme changes
        # This should be handled by the cache invalidation system

        # Test theme switching functionality

        # Switch between themes and verify template resolution
        themes = ["harvard", "cambridge", "oxford", "classic", "corporative"]

        from now_lms.cache import cache

        config = database.session.execute(database.select(Style)).first()[0]

        for theme in themes:
            # Clear cache to ensure fresh theme resolution
            cache.clear()

            config.theme = theme
            database.session.commit()

            # Verify template resolution works
            home_template = get_home_template()
            assert theme in home_template
            assert "overrides/home.j2" in home_template

    for s in ("/", "/course/explore", "/program/explore"):
        response = client.get(s)
        assert response.status_code == 200

    with lms_application.app_context():
        # Restore original theme
        config = database.session.execute(database.select(Style)).first()[0]
        config.theme = "now_lms"
        database.session.commit()

        # Verify default templates are used when no override exists
        cache.clear()  # Clear cache to get fresh template resolution
        assert get_home_template() == "inicio/home.html"
