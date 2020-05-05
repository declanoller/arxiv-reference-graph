import os, shutil, json
import parse_utils as pu
import path_utils

title_db_json = 'title_db.json'
if not os.path.exists(title_db_json):
	print('db file {title_db_json} DNE! Creating it now.')
	empty_dict = {}
	with open(title_db_json, 'w') as f:
		json.dump(empty_dict, f, indent=4)


def get_bbl_from_dir(dir):

	f_list = os.listdir(dir)

	bbl_files = [f for f in f_list if '.bbl' in f]

	if len(bbl_files) >= 1:
		return os.path.join(dir, bbl_files[0])
	else:
		return None


def get_id_from_title_db(title):
	# Unfortunately, should really read it each time, in case it was added
	# to during this execution.
	title_dict = get_title_dict()

	c_t = pu.clean_title(title)

	if c_t in title_dict.keys():
		return title_dict[c_t]
	else:
		return None


def write_id_to_title_db(title, id):

	title_dict = get_title_dict()

	c_t = pu.clean_title(title)

	if c_t not in title_dict.keys():
		title_dict[c_t] = id

		with open(title_db_json, 'w') as f:
			json.dump(title_dict, f, indent=4)


def get_title_dict():
	with open(title_db_json, 'r') as f:
		title_dict = json.load(f)

	return title_dict






















#
