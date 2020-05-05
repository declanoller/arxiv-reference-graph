import os, shutil, re, time, random, json
from urllib import request
from queue import Queue
import traceback as tb
import tarfile
import xmltodict

import parse_utils as pu
import graph_utils as gu
import db_utils as dbu
import path_utils



def fetch_pdf_from_url(url):

	base_pdf_name = url.split('/')[-1]
	fname = os.path.join(path_utils.get_pdfs_dir(), base_pdf_name)
	try:
		#print('Fetching {} into {}...'.format(url, fname))
		req = request.urlopen(url, None, 10)
		#print('Done! Saving...')
		with open(fname, 'wb') as fp:
			shutil.copyfileobj(req, fp)
		#print('Done!')
		return fname
	except:
		print('\n\nSomething failed:')
		print(tb.format_exc())
		print('\n')

	return None


def fetch_source_from_url(url):

	base_source_name = url.split('/')[-1]
	raw_tar_fname = os.path.join(path_utils.get_sources_dir(), base_source_name)
	unpacked_dir = os.path.join(path_utils.get_unpacked_sources_dir(), base_source_name)

	#print('Fetching {} into {}...'.format(url, raw_tar_fname))
	try:
		req = request.urlopen(url, None, 10)
		#print('Done! Saving...')
		with open(raw_tar_fname, 'wb') as fp:
			shutil.copyfileobj(req, fp)

		#print('Done! Unpacking...')

		os.mkdir(unpacked_dir)
		tar = tarfile.open(raw_tar_fname)
		tar.extractall(unpacked_dir)
		tar.close()
		#print('Done!')

		return unpacked_dir
	except:
		print('\n\nSomething failed:')
		print(tb.format_exc())
		print('\n')

	return None


def fetch_pdf_from_id(id):

	fname = pu.pdf_fname_from_id(id)

	if not os.path.exists(fname):
		url = pu.get_pdf_url_from_id(id)
		fname = fetch_pdf_from_url(url)
		time.sleep(0.25 + random.uniform(0,0.2))

	return fname


def get_source_from_id(id):

	base_name = id
	source_dir = os.path.join(path_utils.get_unpacked_sources_dir(), base_name)

	if os.path.exists(source_dir):
		#print(f'source for id {id} already exists, skipping retrieval')
		pass
	else:
		url = pu.get_source_url_from_id(id)
		source_dir = fetch_source_from_url(url)
		time.sleep(0.25 + random.uniform(0,0.2))

	return source_dir



def get_refs_from_id(id):

	# First try seeing if there's a source/bbl file, which is much easier
	# to parse. If not, convert pdf to text and do some nasty parsing.
	source_dir = get_source_from_id(id)
	bbl_file = dbu.get_bbl_from_dir(source_dir)

	if bbl_file is not None:
		ref_info_dicts = pu.get_refs_from_bbl_file(bbl_file)

	else:

		# If we can't get the pdf at all, just skip this one.
		fname = fetch_pdf_from_id(id)
		if fname is None:
			return []

		ref_info_dicts = pu.get_refs_from_pdf_file(fname)
		bbl_file = 'from_pdf'


	return ref_info_dicts, bbl_file



def fetch_title_from_id(id):


	url = 'http://export.arxiv.org/api/query?search_query=id:{}&start=0&max_results=1'.format(id)
	data = request.urlopen(url).read()
	#print(data)
	time.sleep(0.05 + random.uniform(0,0.1))

	d = xmltodict.parse(data)

	if 'entry' not in d['feed'].keys():
		return None

	title = d['feed']['entry']['title']
	title_lc = title.lower()

	year = d['feed']['entry']['published'][:4]

	return {'title_full' : title, 'title_clean' : title_lc, 'year' : year}


def get_id_from_title(title):

	id = None

	try:

		id_db = dbu.get_id_from_title_db(title)

		if id_db is not None:
			id = id_db
		else:

			cleaned_title = '%22{}%22'.format(title.replace('  ', ' ').replace(' ', '+').replace('-', '+').replace('”', '').replace('–', '+'))
			#print(cleaned_title)

			url = 'http://export.arxiv.org/api/query?search_query=ti:{}&start=0&max_results=1'.format(cleaned_title)
			data = request.urlopen(url).read()
			#print(data)
			time.sleep(0.05 + random.uniform(0,0.1))

			d = xmltodict.parse(data)

			if 'entry' not in d['feed'].keys():
				#print(f'No matching entry for title {title} found! Continuing...')
				return None

			url = d['feed']['entry']['id']
			id = pu.get_id_from_arxiv_url(url)
			#year = d['feed']['entry']['published'][:4]

			dbu.write_id_to_title_db(title, id)

	except:
		print('\n\nSomething went wrong! Error:\n')
		print(tb.format_exc())

		#print('\n\nData that caused it:\n')
		#print(data)
		print('\n\nurl that caused it:\n')
		print(url)
		print('\n\ntitle that caused it:\n')
		print(title)
		print('\n\n')
		print('Continuing...\n\n')


	return id


def save_title_db_dict(d):

	root_id = [v['id'] for v in d.values() if v['depth']==0][0]
	date_str = path_utils.get_date_str()

	fname = 'title_dict_id_{}_runtime_{}.json'.format(root_id, date_str)

	with open(fname, 'w') as f:
		json.dump(d, f, indent=4)



def create_reference_graph(base_url, max_depth=2):

	base_id = pu.get_id_from_arxiv_url(base_url)

	title_dict = fetch_title_from_id(base_id)
	dbu.write_id_to_title_db(title_dict['title_clean'], base_id)
	title_info_dict = 	{
							title_dict['title_clean'] : {
											'id' : base_id,
											'depth' : 0,
											'children_titles' : [],
											'status' : 'root',
											'title_full' : title_dict['title_full'],
											'link' : base_url,
											'n_parents' : 0,
											'year' : title_dict['year'],
										}
						}



	# Setup queue for FIFO processing
	title_expand_queue = Queue()
	title_expand_queue.put(title_dict['title_clean'])

	max_depth_reached = 0
	graph_build_stats = None

	while not title_expand_queue.empty():

		title = title_expand_queue.get()

		cur_depth = title_info_dict[title]['depth']

		# printing/diagnostics
		if cur_depth > max_depth_reached:

			if graph_build_stats is not None:
				print('\nEnd of current depth. Build stats:')
				print('Nodes expanded = {}'.format(graph_build_stats['nodes_expanded']))
				print('Nodes unexpanded = {}'.format(graph_build_stats['nodes_unexpanded']))
				print('Nodes other = {}'.format(graph_build_stats['nodes_other']))

			print(f'\nNow at depth {cur_depth}, {title_expand_queue.qsize()} nodes in queue...\n')
			max_depth_reached = cur_depth
			graph_build_stats = {
									'nodes_expanded' : 0,
									'nodes_unexpanded' : 0,
									'nodes_other' : 0,
								}


		# Get arxiv id. If it's not an arxiv article, or it can't find it from
		# the title, id will be None.
		id = get_id_from_title(title)
		title_info_dict[title]['id'] = id
		if id is None:
			title_info_dict[title]['status'] = 'no_id'
			print(f'Couldnt find id for title "{title}", continuing...')
			graph_build_stats['nodes_unexpanded'] += 1
			continue

		# Add a link if possible.
		title_info_dict[title]['link'] = pu.get_arxiv_url_from_id(title_info_dict[title]['id'])

		# If we're at the max depth, set that status and continue.
		if cur_depth >= max_depth:
			title_info_dict[title]['status'] = 'max_depth'
			#print(f'title "{title}" is at max depth of {max_depth}! Continuing...')
			graph_build_stats['nodes_unexpanded'] += 1
			continue

		# If we reach this point, we're not at the max depth and it does have
		# an id, so it's expanded.
		if title_info_dict[title]['status'] is None:
			title_info_dict[title]['status'] = 'expanded'
			graph_build_stats['nodes_expanded'] += 1


		# Get refs for this id.
		ref_info_dicts, bbl_file = get_refs_from_id(id)
		title_info_dict[title]['children_titles'] = [r['ref_title_clean'] for r in ref_info_dicts]
		title_info_dict[title]['children_full_dicts'] = ref_info_dicts
		title_info_dict[title]['refs_source'] = bbl_file

		#title_info_dict[id]['children_ids'] = refs_ids
		#print('{} ids out of {} titles found.'.format(len(refs_ids), len(refs)))

		# Add new node dicts to queue.
		for r in ref_info_dicts:
			if r['ref_title_clean'] not in title_info_dict.keys():
				title_info_dict[r['ref_title_clean']] = {
															'id' : None,
															'depth' : cur_depth+1,
															'children_titles' : [],
															'status' : None,
															'title_full' : r['ref_title_full'],
															'link' : 'none',
															'n_parents' : 1,
															'year' : r['year'],
														}
				title_expand_queue.put(r['ref_title_clean'])
			else:
				title_info_dict[r['ref_title_clean']]['n_parents'] += 1


	save_title_db_dict(title_info_dict)
	gu.convert_title_dict_to_graph(title_info_dict)

	return title_info_dict











#
