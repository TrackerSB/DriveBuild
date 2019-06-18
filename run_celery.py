from celery import Celery, current_app

celery = Celery(current_app._get_current_object())
celery.config_from_object("celeryconfig")
