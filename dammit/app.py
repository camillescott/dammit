# Copyright (C) 2015-2018 Camille Scott
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license.  See the LICENSE file for details.

import argparse
import glob
import logging
import os
import sys
import subprocess
import yaml

from dammit import databases
from dammit import log
from dammit import utils
from dammit import ui
from dammit.meta import __version__, __authors__, __description__, __date__, __path__, get_config


class DammitApp(object):

<<<<<<< HEAD
=======
    def __init__(self, arg_src=sys.argv[1:]):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.config_d, self.databases_d, self.pipeline_d  = get_config()
        self.parser = self.get_parser()

        self.args = self.parser.parse_args(arg_src)
        if hasattr(self.args, 'config_file') and self.args.config_file is not None:
            with open(self.args.config_file) as fp:
                self.config_d.update(yaml.safe_load(fp))
        self.config_d.update(vars(self.args))

    def run(self):
        print(ui.header('dammit'))
        print(ui.header(__description__, level=2))
        about = '\nby {0}\n\n**v{1}**, {2}\n'.format(', '.join(__authors__),
                                           __version__, __date__)
        print(about)
        return self.args.func()

    def description(self):
        return ui.header('dammit: ' + __description__)

    def epilog(self):
        return 'Available BUSCO groups are: '\
               '{0}'.format(', '.join(sorted(self.databases_d['BUSCO'].keys())))

    def get_parser(self):
        '''
        Build the main parser.
        '''
        parser = argparse.ArgumentParser(
                 description=self.description(),
                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.set_defaults(func=parser.print_help)

        parser.add_argument('--debug', action='store_true', default=False)
        parser.add_argument('--version', action='version',
                            version='%(prog)s ' + __version__)
        subparsers = parser.add_subparsers(title='dammit subcommands')

        def add_common_args(parser):
            ''' Add shared options to a parser.

            Shared options are added this way instead of to the main parser
            because I'd rather they come after the subcommand name.

            Args:
                parser (object): The parser to which arguments will be added.
            '''
            parser.add_argument('--database-dir',
                                default=databases.default_database_dir(self.logger),
                                help='Directory to store databases. Existing'\
                                     ' databases will not be overwritten.'\
                                     ' By default, the database directory is'\
                                     ' $HOME/.dammit/databases.'
                                )

            parser.add_argument('--busco-groups',
                                default=['metazoa'],
                                nargs="*",
                                metavar='[metazoa, eukaryota, vertebrata, ...]',
                                choices=list(self.databases_d['BUSCO'].keys()),
                                help='Space separated list of BUSCO group(s)'\
                                     ' to use. Should be chosen'\
                                     ' based on the organism being annotated.'\
                                     ' Full list of options is below.'
                                )

            parser.add_argument('--n_threads',
                                type=int,
                                default=1,
                                help='For annotate, number of threads to pass to '\
                                     'programs  supporting multithreading. For '\
                                     'databases, number of simultaneous tasks '\
                                     'to execute.'
                                )

            parser.add_argument('--config-file',
                                help='A YAML or JSON file providing values to override'\
                                     ' built-in config. Advanced use only!'
                                )

            parser.add_argument('--busco-config-file',
                                help='Path to an alternative BUSCO config'\
                                     ' file; otherwise, BUSCO will attempt'\
                                     ' to use its default installation'\
                                     ' which will likely only work on'\
                                     ' bioconda. Advanced use only!')

            parser.add_argument('--verbosity',
                                default=0,
                                type=int,
                                choices=[0,1,2],
                                help='Verbosity level for doit tasks.'
                                )

            parser.add_argument('--profile',
                                default=False,
                                action='store_true',
                                help='Profile task execution.')

            parser.add_argument('--force',
                                default=False,
                                action='store_true',
                                help='Ignore missing database tasks.')

            parser.add_argument('--no-rename',
                                default=False,
                                action='store_true',
                                help='Keep original transcript names.'\
                                     ' Note: make sure your transcript names'\
                                     ' do not contain unusual characters.')

            parser.add_argument('--pipeline',
                                default='default',
                                choices=["default", "quick", "full", "nr"],
                                help='Which pipeline to use. Pipeline options:'\
                                     ' quick: excludes: '
                                     ' the Infernal Rfam tasks, the HMMER'\
                                     ' Pfam tasks, and the LAST OrthoDB'\
                                     ' and uniref90 tasks. Best for users'\
                                     ' just looking to get basic stats'\
                                     ' and conditional reciprocal best'\
                                     ' LAST from a protein database.'\
                                     ' \nfull: '\
                                     'Run a "complete" annotation; includes'\
                                     ' uniref90, which is left out of the'\
                                     ' default pipeline because it is huge'\
                                     ' and homology searches take a long'\
                                     ' time.'
                                     ' nr: '\
                                     ' Also include annotation to NR database, which'\
                                     ' is left out of the default and "full"'\
                                     ' pipelines because it is huge and'\
                                     ' homology searches take a long time.'\
                                     ' More info  at https://dib-lab.github.io/dammit.'
                                )

        '''
        Add the databases subcommand.
        '''
        desc = '''Check for databases and optionally download and prepare them
               for use. By default, only check their status.'''
        databases_parser = subparsers.add_parser(
                               'databases',
                                description=desc,
                                epilog=self.epilog(),
                                help=desc,
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                )

        databases_parser.add_argument('--install',
                                      action='store_true',
                                      default=False,
                                      help='Install missing databases. Downloads'
                                           ' and preps where necessary'
                                      )

        add_common_args(databases_parser)
        databases_parser.set_defaults(func=self.handle_databases)

        '''
        Add the annotation subcommand.
        '''
        desc = '''The main annotation pipeline. Calculates assembly stats;
               runs BUSCO; runs LAST against OrthoDB (and optionally uniref90),
               HMMER against Pfam, Inferal against Rfam, and Conditional Reciprocal
               Best-hit Blast against user databases; and aggregates all results in
               a properly formatted GFF3 file.'''
        annotate_parser = subparsers.add_parser(
                              'annotate',
                              usage='%(prog)s <transcriptome> [OPTIONS]',
                              description=desc,
                              epilog=self.epilog(),
                              help=desc,
                              formatter_class=argparse.ArgumentDefaultsHelpFormatter
                              )

        annotate_parser.add_argument('transcriptome',
                                     help='FASTA file with the transcripts to be'\
                                          ' annotated.'
                                     )

        annotate_parser.add_argument('-n', '--name',
                                     default='Transcript',
                                     help='Base name to use for renaming the'\
                                          ' input transcripts. The new names'\
                                          ' will be of the form <name>_<X>.'\
                                          ' It should not have spaces, pipes,'\
                                          ' ampersands, or other characters'\
                                          ' with special meaning to BASH.'
                                     )

        annotate_parser.add_argument('-e', '--evalue',
                                     default=1e-5,
                                     type=float,
                                     help='e-value cutoff for similarity'\
                                          ' searches.'
                                     )

        annotate_parser.add_argument('-o', '--output-dir',
                                     default=None,
                                     help='Output directory. By default this will'\
                                          ' be the name of the transcriptome file'\
                                          ' with `.dammit` appended'
                                     )

        annotate_parser.add_argument('--user-databases',
                                     nargs='+',
                                     default=[],
                                     help='Optional additional protein databases. '\
                                          ' These will be searched with CRB-blast.'
                                     )

        annotate_parser.add_argument('--sshloginfile',
                                     default=None,
                                     help='Distribute execution across the specified nodes.')


        add_common_args(annotate_parser)
        annotate_parser.set_defaults(func=self.handle_annotate)

        return parser

    def generate_targets(self, db=False, annot=False):
        pipeline_info = self.pipeline_d["pipelines"][self.args.pipeline]
        targets=[]
        userdbs = {}
        db_dir,out_dir="",""
        # set database_dir
        if self.args.database_dir:
            db_dir = self.args.database_dir
        else:
            db_dir = self.config_d["db_dir"]
        # generate database targets
        databases = pipeline_info.get("databases", None)
        if db and databases:
            #if "BUSCO" in databases:
            #    out_suffix = self.databases_d["BUSCO"]["output_suffix"][0] #donefile
            #    busco_dbinfo = self.databases_d["BUSCO"] #get busco database info
            #    targets = [busco_dbinfo[db]["folder"] + out_suffix for db in list(self.args.busco_groups)]
            #    databases.remove("BUSCO")
            for db in databases:
                fn = self.databases_d[db]["filename"]
                #out_suffixes = [""] # testing: ONLY DOWNLOAD
                out_suffixes = self.databases_d[db]["output_suffix"]
                targets += [fn + suffix for suffix in out_suffixes]
            targets = [os.path.join(db_dir, targ) for targ in targets]

        # generate annotation targets
        if annot:
            if any([self.args.transcriptome.endswith(".fa"),
                    self.args.transcriptome.endswith(".fasta")]):
                transcriptome_name = os.path.basename(self.args.transcriptome).rsplit(".fa")[0]
            else:
                raise ValueError('input transcriptome file must end with ".fa" or ".fasta"')

            if self.args.output_dir:
                out_dir = self.args.output_dir
            else:
                out_dir = transcriptome_name + self.config_d["dammit_dir"]

            annotation_programs = pipeline_info["programs"]
            annotation_databases = pipeline_info.get("databases", [])
            output_suffixes = []
            # not complete yet. need to include database name in annotation targ, where relevant
            # not sure how to represent this in the config.yml. databases arg for prog?

            # handle user databases. currently not downloading - just using local dbs
            user_databases = self.args.user_databases
            for udb in user_databases:
                # should we check if the file exists?
                udb_path = os.path.abspath(os.path.expanduser(udb)) # get absolute path, expanding any `~`
                udb_name = os.path.basename(udb_path)
                userdbs[udb_name] = udb_path

            #handle busco_groups
            busco_lineages = self.args.busco_groups
            # build annotation targets
            for prog in annotation_programs:
                prog_suffixes = self.config_d[prog]["output_suffix"]
                prog_databases = self.config_d[prog].get("databases")
                if prog_databases:
                    # now handle other databases. Only consider databases we're running in this pipeline
                    dbs_to_add = [db for db in prog_databases if db in annotation_databases]
                    # expand __database__ with appropriate databases
                    prog_suffixes = [suffix.replace("__userdatabase__", db) for db in userdbs.keys() for suffix in prog_suffixes]
                    if dbs_to_add:
                        prog_suffixes = [suffix.replace("__database__", db) for db in dbs_to_add for suffix in prog_suffixes]
                    if busco_lineages:
                        prog_suffixes = [suffix.replace("__buscolineage__", db) for db in busco_lineages for suffix in prog_suffixes]
                        print(prog_suffixes)
                output_suffixes.extend(prog_suffixes)
            annotate_targets = [os.path.join(out_dir, transcriptome_name + suffix) for suffix in output_suffixes]
            targets+=annotate_targets
        return targets, db_dir, out_dir, userdbs

    def handle_databases(self):
        log.start_logging()
        print(ui.header('submodule: databases', level=2))

        workflow_file = os.path.join(__path__, 'workflows', 'dammit.snakefile')
        config_file = os.path.join(__path__, 'config.yml')
        full_config = utils.read_yaml(config_file)
        cmd = ["snakemake", "-s", workflow_file] #, "--configfile", config_file]

        db_targets, db_dir, out_dir, userdbs = self.generate_targets(db=True)
        #handle user-specified database dir properly
        # note if `--config` is last arg, it will try to add the workflow targets (targets) to config (and fail)
        #config = ["--config", f"db_dir={db_dir}"]
        #cmd.extend(config)
        additional_config = {"db_dir": db_dir}
        utils.update_nested_dict(full_config, additional_config) # overkill for just this.
        #if userdbs: # add this if we enable user db download
        #    full_config["user_dbs"] = userdbs
        #print workflow configfile
        workflow_configfile = os.path.join(__path__, ".rundammit") # Where to put this file? Current path? Outdir for this run?
        sys.stderr.write(f"Writing full config to {workflow_configfile}\n")
        utils.write_yaml(full_config, workflow_configfile)

        # add configfile to run command
        cmd.extend(["--configfiles", workflow_configfile])

        helpful_args = ["-p", "--nolock", "--use-conda", "--rerun-incomplete", "-k", "--cores", f"{self.args.n_threads}"]
        cmd.extend(helpful_args)

        # better way to do this?
        if not self.args.install:
            cmd.append("--dry_run")

        # finally, add targets
        cmd.extend(db_targets)
        print("Command: " + " ".join(cmd))

        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            print(f'Error in snakemake invocation: {e}', file=sys.stderr)
            return e.returncode

>>>>>>> origin/add_shmlast_wrapper
    def handle_annotate(self):
        log.start_logging()
        print(ui.header('submodule: annotate', level=2))

        workflow_file = os.path.join(__path__, 'workflows', 'dammit.snakefile')
        config_file = os.path.join(__path__, 'config.yml')

        full_config = utils.read_yaml(config_file)
        cmd = ["snakemake", "-s", workflow_file] #, "--configfile", config_file]

        if self.config_d['force'] is True:
            annot_targets, db_dir, out_dir, userdbs = generate_targets(db=True, annot=True)
            utd_msg = '*All database tasks up-to-date.*'
            ood_msg = '*Some database tasks out-of-date; '\
                      'FORCE is True, ignoring!'
        #    uptodate, statuses = db_handler.print_statuses(uptodate_msg=utd_msg,
        #                                                   outofdate_msg=ood_msg)
        else:
            annot_targets, db_dir, out_dir, userdbs = self.generate_targets(annot=True)
            #databases.check_or_fail(db_handler)

        #handle user-specified database dir and output dir properly
        # note if `--config` is last arg, it will try to add the workflow targets (targets) to config (and fail)
        #config = ["--config", f"db_dir={db_dir}", f"dammit_dir={out_dir}", f"input_transcriptome={self.args.transcriptome}"]
        #cmd.extend(config)

        #build config to write out instead
        additional_config = {"db_dir": db_dir, "dammit_dir": out_dir, "input_transcriptome": self.args.transcriptome}
        # update full config
        utils.update_nested_dict(full_config, additional_config)
        if userdbs:
            full_config["user_dbs"] = userdbs

        workflow_configfile = os.path.join(__path__, ".rundammit") # Where to put this file? Current path? Outdir for this run?
        sys.stderr.write(f"Writing full config to {workflow_configfile}\n")
        utils.write_yaml(full_config, workflow_configfile)
        # add configfile to run command
        cmd.extend(["--configfiles", workflow_configfile])

        # move these to a default dammit run profile?
        helpful_args = ["-p", "--nolock", "--use-conda", "--rerun-incomplete", "-k", "--cores", f"{self.args.n_threads}"]
        cmd.extend(helpful_args)

        # finally, add targets
        cmd.extend(annot_targets)

        print("Command: " + " ".join(cmd))
        try:
            subprocess.check_call(["snakemake","--version"])
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            print(f'Error in snakemake invocation: {e}', file=sys.stderr)
            return e.returncode
