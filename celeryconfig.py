# Celery
# CELERY_ACCEPT_CONTENT = ["pickle"]
# CELERY_TASK_SERIALIZER = ["pickle"]
# CELERY_RESULT_SERIALIZER = ["pickle"]
BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_IGNORE_RESULT = False
CELERY_TRACK_STARTED = True
CELERY_IMPORTS = ("sim_controller", "app")
