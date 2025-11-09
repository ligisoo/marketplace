from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class TipsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tips'

    def ready(self):
        """
        Called when Django starts.
        Start the background task queue.
        """
        # Only start in main process (avoid running in migrations, management commands, etc.)
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            try:
                from .task_queue import get_task_queue
                queue = get_task_queue()
                logger.info("Background task queue started successfully")
            except Exception as e:
                logger.error(f"Failed to start task queue: {str(e)}")
