#!/usr/bin/env python
from __future__ import print_function

from itertools import count 
import json
import logging
import os
import pprint
import re
from shutil import rmtree
import shutil
import sys

from doit.action import CmdAction
from doit.tools import run_once, create_folder, title_with_actions, LongRunning
from doit.task import clean_targets, dict_to_task

import pandas as pd
from khmer import HLLCounter, ReadParser
from shmlast.hits import BestHits
from shmlast.last import MafParser

from .utils import which, doit_task
from . import parsers
from . import gff


def clean_folder(target):
    try:
        rmtree(target)
    except OSError:
        pass



@doit_task
def get_group_task(group_name, tasks):

    return {'name': group_name,
            'actions': None,
            'task_dep': [t.name for t in tasks]}

@doit_task
def get_maf_best_hits_task(maf_fn, output_fn):

    hits_mgr = BestHits()

    def cmd():
        df = MafParser(maf_fn).read()
        df = hits_mgr.best_hits(df)
        df.to_csv(output_fn, index=False)

    name = 'maf_best_hits:{0}-{1}'.format(maf_fn, output_fn)

    return {'name': name,
            'title': title_with_actions,
            'actions': [cmd],
            'targets': [output_fn],
            'file_dep': [maf_fn],
            'clean': [clean_targets]}






   
@doit_task
def get_maf_gff3_task(input_filename, output_filename, database):

    name = 'maf-gff3:' + os.path.basename(output_filename)

    def cmd():
        if input_filename.endswith('.csv') or input_filename.endswith('.tsv'):
            it = pd.read_csv(input_filename, chunksize=10000)
        else:
            it = MafParser(input_filename)

        with open(output_filename, 'a') as fp:
            for group in it:
                gff_group = gff.maf_to_gff3_df(group, database=database)
                gff.write_gff3_df(gff_group, fp)

    return {'name': name,
            'title': title_with_actions,
            'actions': ['rm -f {0}'.format(output_filename),
                        cmd],
            'file_dep': [input_filename],
            'targets': [output_filename],
            'clean': [clean_targets]}


@doit_task
def get_crb_gff3_task(input_filename, output_filename, database):

    name = 'crbb-gff3:' + os.path.basename(output_filename)

    def cmd():
        with open(output_filename, 'a') as fp:
            for group in parsers.crb_to_df_iter(input_filename,
                                                remap=True):
                gff_group = gff.crb_to_gff3_df(group, database=database)
                gff.write_gff3_df(gff_group, fp)

    return {'name': name,
            'title': title_with_actions,
            'actions': ['rm -f {0}'.format(output_filename),
                        cmd],
            'file_dep': [input_filename],
            'targets': [output_filename],
            'clean': [clean_targets]}


@doit_task
def get_hmmscan_gff3_task(input_filename, output_filename, database):

    name = 'hmmscan-gff3:' + os.path.basename(output_filename)

    def cmd():
        with open(output_filename, 'a') as fp:
            for group in pd.read_csv(input_filename, chunksize=10000):
                gff_group = gff.hmmscan_to_gff3_df(group, database=database)
                gff.write_gff3_df(gff_group, fp)

    return {'name': name,
            'title': title_with_actions,
            'actions': ['rm -f {0}'.format(output_filename),
                        cmd],
            'file_dep': [input_filename],
            'targets': [output_filename],
            'clean': [clean_targets]}


@doit_task
def get_cmscan_gff3_task(input_filename, output_filename, database):

    name = 'cmscan-gff3:' + os.path.basename(output_filename)

    def cmd():
        with open(output_filename, 'a') as fp:
            for group in parsers.cmscan_to_df_iter(input_filename):
                gff_group = gff.cmscan_to_gff3_df(group, database=database)
                gff.write_gff3_df(gff_group, fp)

    return {'name': name,
            'title': title_with_actions,
            'actions': ['rm -f {0}'.format(output_filename),
                        cmd],
            'file_dep': [input_filename],
            'targets': [output_filename],
            'clean': [clean_targets]}


@doit_task
def get_gff3_merge_task(gff3_filenames, output_filename):

    name = 'gff3-merge:{0}'.format(os.path.basename(output_filename))

    merge_cmd = 'echo "{v}" > {out}; cat {f} | sed \'/^#/ d\''\
                ' | sort | sed \'/^$/d\' >> {out}'.format(v=gff.version_line(),
                                          f=' '.join(gff3_filenames),
                                          out=output_filename)
    return {'name': name,
            'title': title_with_actions,
            'actions': [merge_cmd],
            'file_dep': gff3_filenames,
            'targets': [output_filename],
            'clean': [clean_targets]}

