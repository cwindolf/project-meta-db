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
def add_images(relative_paths, dataset, channels=None, dimensions=None,
			   cifs_mount='/media/data_cifs/'):
	'''add_images

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
	return images


@db_session
def add_label(rel_path, image, label_type, dataset=None):
	'''add_label
	
	Add a single label to a single image.

	Arguments:
		rel_path 		str
			The path relative to the CIFS mount where this label lives.
		image 			str or Image
			Either an Image, or the relative path of an image that already
			exists in the DB.
		label_type 		str
			Lowercase str like `depth` or `surface_normals`
		dataset 		Dataset or None
			If None, use `image`'s associated Dataset.
	Returns:
		The new Label object.
	'''
	if image is not None and not isinstance(image, Image):
		image = Image.get(rel_path=image)
	if image is None:
		raise ValueError('`image` needs to exist in the database.')
	if dataset is None:
		dataset = image.dataset
	return Label(rel_path=rel_path, image=image,
		         dataset=dataset, type=label_type)


@db_session
def add_labels(relative_paths, dataset, label_type, images=None):
	'''add_labels

	Given a Dataset `dataset` and the relative paths on	the CIFS mount for its
	labels, load up all of `dataset`'s images and associate each label here
	to one of these images. In particular, ensure that `len(relative_paths)`
	equals the number of images associated to `dataset`. Label-image pairs
	will be chosen by zipping sorted arrays of relative paths, so a good
	naming scheme should be chosen. For more control, look at `add_label`,
	which manually associates a label to a given image, and is called by
	this function.

	On the other hand, if images is not None, and if it is a list of strings,
	we assume that it is a list of pre-sorted relative paths corresponding
	to images that already exist in the dataset. This function also accepts
	a list of Image objects here, again assuming that it is sorted the
	same way as `relative_paths`.

	Arguments:
		relative_paths		[str]
			A list containing the relative path on the CIFS mount for each
			label.
		dataset 			str or Dataset
			Either the name of an already-existing Dataset, or a Dataset
			object, to which these labels will be added.
		label_type 			str
			What kind of labels are these? Use a lowercase string like
			`depth`, `surface_normals`, etc.
		images 				[str] or [Image]
			A list of Image objects or relative paths to images which must
			already exist in the DB. Assumed to be ordered the same way as
			`relative_paths` so that images can be associated to the label at
			the same position in `relative_paths`.
	Returns:
		A list of the new Label objects.
	'''
	# Get dataset in order
	if not isinstance(dataset, Dataset):
		dataset = Dataset.get(name=dataset)
		if dataset is None:
			raise ValueError('dataset should already exist')
	# Get images in order
	if images is None:
		images = sorted(dataset.images, key=lambda i: i.rel_path)
	elif not isinstance(images[0], Image):
		# If not list of Image, interpret as list of rel paths
		images = sorted(images)
		for i in range(len(images)):
			images[i] = Image.get(rel_path=images[i])
			if images[i] is None:
				raise ValueError('relative paths in `images` should correspond'
					             ' to images that have already been stored')
	# Make labels
	if len(images) != len(relative_paths):
		raise ValueError('The dataset should have an image for each label.')
	return [add_label(rp, im, label_type, dataset)
	        for rp, im in zip(relative_paths, images)]


