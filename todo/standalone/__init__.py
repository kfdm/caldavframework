import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "todo.standalone.settings")

import logging

logging.basicConfig(level=logging.DEBUG)
