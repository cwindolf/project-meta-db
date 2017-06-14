from datetime import datetime
from pony.orm import *


db = Database()


class DBMeta(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    date = Required(datetime)
    project = Required('Project')
    num_training = Required(int)
    num_test = Required(int)
    num_validation = Required(int)
    validation_data = Required(str)
    training_data = Required(str)
    test_data = Required(str)

class Project(db.Entity):
    id = PrimaryKey(int, auto=True)
    d_b_metas = Set(DBMeta)
    name = Required(str, unique=True)
