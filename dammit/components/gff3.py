# Copyright (C) 2015-2018 Camille Scott
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import shlex
import subprocess

import click

from ..fileio.gff3 import GFF3Writer


@click.command('merge-gff3')
@click.argument('gff3_filenames', nargs=-1)
@click.argument('output_filename')
def merge_gff3_cmd(gff3_filenames, output_filename):
    ''' Merge a collection of GFF3 files.
    \f

    Args:
        gff3_filenames (list): Paths to the GFF3 files.
        output_filename (str): Path to pipe the results.
    '''

    if not gff3_filenames:
        return
    
    version_cmd = 'echo "{v}" > {out}'.format(v=GFF3Writer.version_line,
                                              out=output_filename)
    merge_cmd = 'cat {f} | sed "/^#/ d"'\
                ' | sort | sed "/^$/d" >> {out}'.format(f=' '.join(gff3_filenames),
                                                        out=output_filename)
    subprocess.run(version_cmd, shell=True)
    subprocess.run(merge_cmd, shell=True)
