#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp
import logging, os, collections, shutil
from time import strftime
import svj.genprod
logger = logging.getLogger('root')

class Submitter(object):
    """docstring for Submitter"""
    def __init__(self):
        super(Submitter, self).__init__()
        


class PySubmitter(Submitter):
    """
    Sets up to run a python file
    """
    def __init__(self, pythonfile, tarball=None):
        super(PySubmitter, self).__init__()
        self.pythonfile = osp.abspath(pythonfile)
        self.pythonfile_basename = osp.basename(self.pythonfile)
        self.rundir = osp.join(
            os.getcwd(),
            self.pythonfile_basename.replace('.py', '') + strftime('_%Y%m%d_%H%M%S')
            )

        self.tarball = tarball
        self.seed = 1001
        self.n_jobs = 1
        self.n_events = 20
        self.read_preprocessing_directives()


    def read_preprocessing_directives(self):
        """
        Overwrites some standard class attributes based on possible preprocessing
        directives contained in the python file
        """
        preprocessing = svj.core.utils.read_preprocessing_directives(self.pythonfile)
        if 'tarball' in preprocessing:
            self.tarball = preprocessing['tarball']
            svj.genprod.SVJ_TARBALL = self.tarball
            logger.info(
                'Setting tarball %s based on preprocessing directive in %s',
                self.tarball, self.pythonfile
                )
        if 'n_jobs' in preprocessing:
            self.n_jobs = int(preprocessing['n_jobs'])
            logger.info(
                'Setting n_jobs %s based on preprocessing directive in %s',
                self.n_jobs, self.pythonfile
                )
        if 'n_events' in preprocessing:
            self.n_events = int(preprocessing['n_events'])
            logger.info(
                'Setting n_events %s based on preprocessing directive in %s',
                self.n_events, self.pythonfile
                )
        if 'seed' in preprocessing:
            self.seed = int(preprocessing['seed'])
            logger.info(
                'Setting seed %s based on preprocessing directive in %s',
                self.seed, self.pythonfile
                )


    def submit(self, dry=False):
        svj.core.utils.check_proxy()

        # Setup the rundir
        svj.core.utils.create_directory(self.rundir, must_not_exist=True, dry=dry)
        with svj.core.utils.switchdir(self.rundir, dry=dry):
            # Copy the python file
            logger.info('Copying {0} --> {1}'.format(self.pythonfile, self.pythonfile_basename))
            if not dry: shutil.copyfile(self.pythonfile, self.pythonfile_basename)
            # Make code tarballs
            tarball_core = svj.core.tarball(dry=dry)
            tarball_genprod = svj.genprod.tarball(dry=dry)

            # Generate .sh file
            sh_file = self.pythonfile_basename.replace('.py', '.sh')
            sh = svj.genprod.condor.shfile.SHStandard(python_file = self.pythonfile)
            sh.add_code_tarball(tarball_core)
            sh.add_code_tarball(tarball_genprod)
            sh.to_file(sh_file, dry=dry)

            # Generate .jdl file
            jdl_file = self.pythonfile_basename.replace('.py', '.jdl')
            infiles = [ tarball_core, tarball_genprod ]
            if self.tarball: infiles.append(self.tarball)
            jdl = svj.genprod.condor.jdlfile.JDLStandard(
                sh_file = sh_file,
                python_file = self.pythonfile,
                n_jobs = self.n_jobs,
                n_events_per_job = self.n_events,
                infiles = infiles,
                )
            jdl.to_file(jdl_file, dry)

            # Create also a small script to delete the output and logs
            svj.genprod.condor.shfile.SHClean().to_file('clean.sh', dry=dry)

            # Submit the job
            try:
                from cjm import TodoList
                logger.info('Found installation of cjm')
                if not dry: TodoList().submit(jdl_file)
            except ImportError:
                logger.info('Submitting using plain condor_submit')
                cmd = ['condor_submit', jdl_file]
                svj.core.utils.run_command(jdl_file, dry=dry, shell=True)

