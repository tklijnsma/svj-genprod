#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as osp
import os, logging
from time import strftime
import svj.core
logger = logging.getLogger('root')

#____________________________________________________________________
# Global scope for genprod

SVJ_TOP_DIR = osp.abspath(osp.dirname(__file__))

# Default seed used for lhe generation and fullsim train
SVJ_SEED = 1001

# Input files directory for this package
SVJ_INPUT_DIR = osp.join(SVJ_TOP_DIR, 'input')

# Directory where the CMSSW genproductions package is installed
MG_GENPROD_DIR = None

# Paths to store temporary files
MG_MODEL_DIR = '/tmp/svj/models'
MG_INPUT_DIR = '/tmp/svj/inputs'
RUN_GRIDPACK_DIR = '/tmp/svj/rungridpack'
RUN_FULLSIM_DIR = '/tmp/svj/runfullsim'
SVJ_OUTPUT_DIR = '/tmp/svj/output'

# Assume running locally by default
# This variable will be set to True if using the svjgenprod-batch script
BATCH_MODE = False


#____________________________________________________________________
# Setting module-level global variables based on environment

def read_environment():
    """ Defines a bunch of global variables of the package based on environment """
    env = os.environ

    if 'SVJ_SEED' in env:
        set_seed(env['SVJ_SEED'])
        logger.info(
            'Taking seed from SVJ_SEED environment variable: {0}'
            .format(SVJ_SEED)
            )

    # Path to the genproductions repo installation
    try:
        global MG_GENPROD_DIR
        MG_GENPROD_DIR = env['MG_GENPROD_DIR']
    except KeyError:
        logger.warning(
            '$MG_GENPROD_DIR not set. Tarball generation will not work. '
            'Install the CMSSW genproductions package if you want to generate tarballs.'
            )

    if 'SVJ_BATCH_MODE' in env:
        batch_mode = env['SVJ_BATCH_MODE'].rstrip().lower()
        if batch_mode == 'lpc':
            batch_mode_lpc()
        else:
            raise ValueError(
                'Unknown batch mode {0}. If you are not trying '
                'to run on a batch system, unset the SVJ_BATCH_MODE '
                'environment variable.'
                .format(batch_mode)
                )

def batch_mode_lpc():
    global BATCH_MODE
    BATCH_MODE = True
    try:
        scratch_dir = os.environ['_CONDOR_SCRATCH_DIR']
        global MG_MODEL_DIR
        global MG_INPUT_DIR
        global RUN_GRIDPACK_DIR
        global RUN_FULLSIM_DIR
        global SVJ_OUTPUT_DIR
        MG_MODEL_DIR     = osp.join(scratch_dir, 'svj/models')
        MG_INPUT_DIR     = osp.join(scratch_dir, 'svj/inputs')
        RUN_GRIDPACK_DIR = osp.join(scratch_dir, 'svj/rungridpack')
        RUN_FULLSIM_DIR  = osp.join(scratch_dir, 'svj/runfullsim')
        SVJ_OUTPUT_DIR   = osp.join(scratch_dir, 'output')
    except KeyError:
        logger.error(
            'Attempted to setup for batch mode (lpc), but ${_CONDOR_SCRATCH_DIR} is not set.'
            )
        raise

def set_seed(seed):
    global SVJ_SEED
    SVJ_SEED = int(seed)
    logger.info('Setting seed to {0}'.format(SVJ_SEED))

read_environment()

#____________________________________________________________________
# Convenience global scope functions

def tarball(outfile=None, dry=False):
    """ Wrapper function to create a tarball of svj.genprod """
    return svj.core.utils.tarball(__file__, outfile=outfile, dry=dry)


#____________________________________________________________________
# Package imports

from . import utils
from .config import Config
from semanager import SEManager
from .gridpackgenerator import GridpackGenerator
from .lhemaker import LHEMaker
import calc_dark_params as cdp

from .gensimfragment import GenSimFragment
from .fullsimbase import FullSimRunnerBase
import fullsimrunners

# import condor.jdlfile
# import condor.shfile
# import condor.submitter

