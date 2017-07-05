from pony.orm import *
from datetime import datetime
from scipy import imread
import os.path
from src.schema import *
from config import DB_TYPE, HOST, USER, DATABASE, PASSWORD


db.bind(DB_TYPE, host=HOST, user=USER, database=DATABASE, password=PASSWORD)
db.generate_mapping()


@db_session
def add_project(name, d_b_metas=None):
	'''add_project

	Add a new project to the projects table.

	Arguments:
		name 	str
				Name of the project
		db_metas
				iterable of Dataset or None
				optional. dbmetas that belong to this project.
	Returns:
		The new Project instance.
	'''
	return Project(name=name, d_b_metas=(d_b_metas if d_b_metas else ()))


@db_session
def add_dataset(name, date, project_name, num_training, num_test,
	            num_validation, training_data_path, test_data_path,
	            validation_data_path):
	'''add_dataset

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
		The new `Dataset` instance.
	'''
	# check if `project_name` corresponds to a project that already exits.
	project = Project.get(name=project_name)
	# if not, let's make one.
	if project is None:
		project = add_project(project_name)
	# if there's no date specified, do now.
	date = date if date else datetime.now()
	# make the Dataset. autosaved by the @db_session
	return Dataset(name=name, date=date, project=project,
				  num_training=num_training, num_validation=num_validation,
				  num_test=num_test, training_data=training_data_path,
				  test_data=test_data_path,
				  validation_data=validation_data_path)

@db_session
def add_images_to_dataset(relative_paths, dataset, channels=None, dimensions=None,
						  cifs_mount='/media/data_cifs/'):
	'''add_images_to_dataset

	Given a list of relative paths, add them to the dataset specified by dataset.
	This doesn't add any labels at the same time, yet.

	Arguments:
		relative_paths	[str]
			A list of strings each pointing to a path relative to the cifs mount.
		dataset 		str OR Dataset
			If string typed, interpret as the name of a dataset.
			If Dataset typed, add to that Dataset.
		channels 		int OR None
			How many channels in each image? If int, use that for every image.
			If None, open the image and see how big its inner axis is.
		dimensions      [int * int] OR None
		    If list of tuples (w, h), use these as image dimensions.
		    If none, open each image and find its dimension.
		cifs_mount		str
			If we need to open images cuz either channels or dimensions is None,
			we'll look here.
	Returns:
		A list of the new `Image` instances.
	'''
	if not isinstance(dataset, Dataset):
		dataset = Dataset.get(name=dataset)
		if dataset is None:
			raise ValueError('dataset should already exist')
	images = []
	for i in range(len(relative_paths)):
		if channels is None or dimensions is None:
			shape = scipy.imread(os.path.join(cifs_mount, relative_paths[i])).shape
			if channels is None:
				c = shape[2]
			if dimensions is None:
				d = shape[0:2]
		elif channels:
			c = channels
		elif dimensions:
			d = dimensions[i]
		images.append(Image(dataset=dataset, rel_path=relative_paths[i],
			                height=d[1], width=d[0], channels=c,
			                extension=os.path.splitext(relative_paths[i])[1],
			                labels=()))
