"""
WSGI-entrypoint voor Foto Nummeraar Online.
"""

from app import create_app

app = create_app("production")
