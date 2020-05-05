import os, re, json, string
import path_utils


def clean_title(title):
	return title.replace('”', '').replace('–', '-').lower()


def linebreak_every_n_spaces(s, n=3):

	# This is to turn every nth space into a newline,
	# for stuff like plotting.
	counter = 0
	while True:
		if counter > n:
			t = s.replace(' ', '\n', 1)
			counter = 0
		else:
			# one that will stay spaces.
			t = s.replace(' ', 'PLACEHOLDERXYZ', 1)
			counter += 1

		if t == s:
			break
		else:
			s = t

	s = s.replace('PLACEHOLDERXYZ', ' ')
	return(s)


def remove_punctuation(s):

	return s.translate(str.maketrans('', '', string.punctuation))


def get_refs_from_bbl_file(bbl_file):

	with open(bbl_file, 'r') as f:
		bbl_text = f.read()

	bib_items = re.split(r'\\bibitem', bbl_text)[1:]

	ref_title_dicts = []

	for b in bib_items:

		blocks = re.split(r'\\newblock ', b)[1:]
		#[print(bl) for bl in blocks]

		# Check for year
		year = 'none'
		for bl in blocks:
			year_find = re.findall(r' \d{4}\.', bl)
			if len(year_find) == 1:
				year = year_find[0][1:-1]

		# Find one that doesn't have a year in it, which is the title one.
		for bl in blocks:
			year_check = re.split(r'\d{4}', bl)
			if len(year_check) == 1:
				if len(bl) < 150:
					title = bl.replace('\n\n', ' ').replace('\n', ' ').replace('-', ' ').replace('  ', ' ').replace('  ', ' ').replace('emph{', '').replace(r'\em', '').replace('{', '').replace('}', '').lstrip().rstrip()
					if title[-1] == '.':
						title = title[:-1]
					title_clean = remove_punctuation(title).lstrip().rstrip().lower()

					ref_title_dicts.append({'ref_title_clean' : title_clean, 'ref_title_full' : title, 'year' : year, 'full_block' : bl})
					break

	#[print(ti) for ti in ref_titles]
	return ref_title_dicts


def get_refs_from_pdf_file(pdf_fname):

	# Convert pdf to txt if it doesn't already exist
	txt_fname = os.path.join('txts', pdf_fname.split('/')[-1].replace('.pdf', '.txt'))
	if not os.path.exists(txt_fname):
		cmd = 'pdftotext {} {}'.format(pdf_fname, txt_fname)
		print(f'Calling command {cmd} to convert to .txt...')
		os.system(cmd)
		print('Done!')

	with open(txt_fname, 'r') as f:
		txt_total = f.read()


	ref_sec_check_strs = ['References', 'REFERENCES', 'R EFERENCES']
	use_ref_str = None
	for ref_str in ref_sec_check_strs:
		ref_section_split = txt_total.split('\n' + ref_str)
		if len(ref_section_split) > 1:
			use_ref_str = ref_str
			ref_section = ref_section_split[-1]
			break

	if use_ref_str is None:
		print(f'Couldnt parse refs for pdf_name: {pdf_name}, returning empty list')
		return []

	ref_section = ref_section.split('\nSupplementary')[0]

	#refs_sep = ref_section.split('.\n')
	refs_sep = re.split(r'\d{4}\.\n', ref_section)
	#ref_titles = [r.split('.')[-2] for r in refs_sep]

	ref_title_dicts = []

	for i,r in enumerate(refs_sep):
		#print(f'\nRef {i}: ', r)
		#print('title list:')
		title_list = r.split('.')
		#print(title_list)
		if len(title_list) >= 2:

			digits_dot_list = re.split(r'\d{4}\.', r)
			pp_dot_list = re.split(r'pp\.', r)

			if len(digits_dot_list) > 1 or len(pp_dot_list) > 1:
				title = title_list[-3]
			else:
				title = title_list[-2]

			#print('\nTitle:', title)
			#title = title.replace('\n', ' ').replace('  ', ' ').lstrip().rstrip().replace('emph{', '').replace('{', '').replace('}', '')
			title = title.replace('\n\n', ' ').replace('\n', ' ').replace('-', ' ').replace('  ', ' ').replace('  ', ' ').replace('emph{', '').replace(r'\em', '').replace('{', '').replace('}', '').lstrip().rstrip()
			if title[-1] == '.':
				title = title[:-1]
			title_clean = remove_punctuation(title).lstrip().rstrip().lower()

			if len(title) < 200:
				ref_title_dicts.append({'ref_title_clean' : title_clean, 'ref_title_full' : title, 'year' : 'none', 'full_block' : r})

	return ref_title_dicts


def get_id_from_arxiv_url(url):
	"""
	examples is http://arxiv.org/abs/1512.08756v2
	we want to extract the raw id and the version
	"""
	ix = url.rfind('/')
	idversion = url[ix+1:].split('v')[0] # extract just the id (and the version)
	return idversion


def get_pdf_url_from_id(id):
	return 'https://arxiv.org/pdf/{}.pdf'.format(id)


def get_arxiv_url_from_id(id):
	return 'https://arxiv.org/abs/{}'.format(id)


def get_source_url_from_id(id):
	return 'https://arxiv.org/e-print/{}'.format(id)



def pdf_fname_from_id(id):
	base_pdf_name = f'{id}.pdf'
	fname = os.path.join('saved_pdfs', base_pdf_name)
	return fname
