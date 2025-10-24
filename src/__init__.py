#!/usr/bin/env

from src.stage0 import app as stage0
from src.stage1.main import app as stage1

from decouple import config

from sqlmodel import SQLModel, create_engine


##########################################################################
# Database Setup
##########################################################################
# Define the name of the SQLite database file
# database_name = config("DATABASE_NAME", "database.db")

# Construct the full SQLite database URL using the defined file name
# sqlite_url = "sqlite:///%s" % database_name
sqlite_url = str(config("DATABASE_NAME", "sqlite:///database.db"))

# Create a SQLAlchemy engine instance for connecting to the SQLite database
# Setting echo=True enables SQL logging for debugging and visibility
engine = create_engine(sqlite_url, echo=True)


# Create all database tables defined in the SQLModel metadata
# This ensures that any models mapped to the database are initialized
def init_db():
    SQLModel.metadata.create_all(engine)
