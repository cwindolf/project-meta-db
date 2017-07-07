from datetime import datetime
from pony.orm import *


db = Database()


class Dataset(db.Entity):
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
    images = Set('Image')
    labels = Set('Label')
    t_f_recordses = Set('TFRecords')


class Project(db.Entity):
    id = PrimaryKey(int, auto=True)
    datasets = Set(Dataset)
    name = Required(str)


class Image(db.Entity):
    id = PrimaryKey(int, auto=True)
    dataset = Required(Dataset)
    rel_path = Required(str)
    height = Required(int, size=32)
    width = Required(int, size=32)
    channels = Required(int, size=32)
    extension = Required(str, 10)
    labels = Set('Label')


class Label(db.Entity):
    id = PrimaryKey(int, auto=True)
    image = Required(Image)
    dataset = Required(Dataset)
    type = Required(str)
    rel_path = Required(str, unique=True)


class TFRecords(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    dataset = Required(Dataset)
    date = Required(datetime)
