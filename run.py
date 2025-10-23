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


# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from loguru import logger

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import lms_app, init_app
from now_lms.worker_config import get_worker_config_from_env

PORT = environ.get("PORT") or 8080

if init_app():
    logger.info("Iniciando NOW Learning Management System")
    try:
        from waitress import serve

        # Get optimal worker and thread configuration
        workers, threads = get_worker_config_from_env()

        logger.info(f"Starting Waitress WSGI server on port {PORT} with {threads} threads")
        serve(
            lms_app,
            host="0.0.0.0",
            port=PORT,
            threads=threads,
            channel_timeout=120,
            cleanup_interval=30,
            _quiet=False,
        )
    except ImportError:
        logger.error("Waitress no está instalado. Por favor instálalo con: pip install waitress")
        logger.error("No se pudo iniciar NOW Learning Management System.")
else:
    logger.error("No se pudo iniciar NOW Learning Management System.")
