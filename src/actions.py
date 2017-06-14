from pony.orm import *
from datetime import datetime
from src.schema import db, DBMeta, Project
from config import DB_TYPE, HOST, USER, DATABASE

db.bind(DB_TYPE, host=HOST, user=USER, database=DATABASE)
db.generate_mapping()


@db_session
def add_project(name, db_metas=None):
	'''add_project

	Add a new project to the projects table.

	Arguments:
		name 	str
				Name of the project
		db_metas
				set of DBMeta or None
				optional. dbmetas that belong to this project.
	Returns:
		The new Project instance.
	'''
	return Project(name, db_metas)


@db_session
def add_database(name, date, project_name, num_training, num_test,
	             num_validation, training_data_path, test_data_path,
	             validation_data_path):
	'''add_database

	Add the metadata for a new packaged dataset to the database. Will
	also create a row in the project database if `project_name` doesn't
	match any of the projects that already exist.
	
	Arguments:
		name 	str
				Describes the dataset
		date 	datetime or None
				A particular date, or None (it will be auto-generated)
		project_name
				str
				The name project that this dataset belongs to.
		num_training, num_test, num_validation
				int
				The number of {training, test, validation} examples 
				contained in this dataset.
		training_data_path, test_data_path, validation_data_path
				str
				The relative file system location of the {training, test,
				validation} data files.

	Returns:
		The new `DBMeta` instance.
	'''
	# check if `project_name` corresponds to a project that already exits.
	project = Project.get(name=project_name)
	# if not, let's make one.
	if project is None:
		project = add_project(project_name)
	# if there's no date specified, do now.
	date = date if date else datetime.now()
	# make the DBMeta. autosaved by the @db_session
	return DBMeta(name=name, date=date, project=project,
				  num_training=num_training, num_validation=num_validation,
				  num_test=num_test, training_data_path=training_data_path,
				  test_data_path=test_data_path,
				  validation_data_path=validation_data_path)

