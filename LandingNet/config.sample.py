import os

basedir = os.path.abspath(os.path.dirname(__file__))
DEBUG = True
SQLALCHEMY_DATABASE_URI = "postgresql://landingnet:password@localhost:5432/landingnet" 
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, "tools", "db_repository")
MINIDUMP_UPDLOAD_DIR = "minidumps"
DEBUG_SYMBOLS_DIR = "debug-symbols"
STACKWALKER = "bin/stackwalker"
