import subprocess
from src.schema import db, DBMeta, Project
from config import DB_TYPE, HOST, USER, DATABASE, PASSWORD


# make sure Pony can bind to it, and create the tables
db.bind(DB_TYPE, host=HOST, user=USER, database=DATABASE, password=PASSWORD)
db.generate_mapping(create_tables=True)
