import os
import envdir

CONFIG_DIR = os.path.expanduser('~/.config/todo')

if os.path.exists(CONFIG_DIR):
    envdir.open(CONFIG_DIR)