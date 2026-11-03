import os
bind = "0.0.0.0:" + os.getenv("PORT", "8000")
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
timeout = 30
errorlog = "-"
# HTTP requests are logged as JSON by the application.
accesslog = None
