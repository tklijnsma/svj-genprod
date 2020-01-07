#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as osp
import os, logging
from time import strftime
import svj.core

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

# Convenience global variable. Will be set by svjgenprod-batch if a tarball
# preprocessing directive is given
SVJ_TARBALL = None

# Overwrite global vars based on environment variables
import environment
# environment.read_environment()

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

import condor.jdlfile
import condor.shfile
import condor.submitter

