from src.schema import db, DBMeta, Project
from config import DB_TYPE, HOST, USER, DATABASE

db.bind(DB_TYPE, host=HOST, user=USER, database=DATABASE)
db.generate_mapping(create_tables=True)