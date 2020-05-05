import os, sys, shutil, json, time
from datetime import datetime

PDFS_DIR = 'saved_pdfs'
SOURCES_DIR = 'saved_sources'
TXTS_DIR = 'txts'
UNPACKED_SOURCES_DIR = 'unpacked_sources'

dirs_list = [PDFS_DIR, SOURCES_DIR, TXTS_DIR, UNPACKED_SOURCES_DIR]

for d in dirs_list:
    if not os.path.exists(d):
        print(f'Dir {d} DNE! Creating it now')
        os.mkdir(d)

def get_pdfs_dir():
    return PDFS_DIR

def get_sources_dir():
    return SOURCES_DIR

def get_txts_dir():
    return TXTS_DIR

def get_unpacked_sources_dir():
    return UNPACKED_SOURCES_DIR


def get_date_str():
    # Returns the date and time for labeling output.
    # -4 to only take two second decimal places.
	return datetime.now().strftime('%d-%m-%Y_%H-%M-%S')


















#
