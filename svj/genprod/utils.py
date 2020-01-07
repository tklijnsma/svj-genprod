#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp
import logging, subprocess, os, shutil, re, pprint, csv
import svj.core
import svj.genprod
logger = logging.getLogger('root')


def crosssection_from_file(file, m_med_target):
    """
    Assumes a two column file with first column m_med, second column xs.
    Does not require any dependencies like this.
    """
    logger.debug('Loading xsec list from file {0}'.format(file))
    with open(file ,'r') as f:
        for line in svj.core.utils.decomment(f):
            m_med, xs = line.split()
            m_med = float(m_med)
            if m_med == m_med_target:
                xs = float(xs)
                logger.debug('Found xs = {0} for m_med = {1}'.format(xs, m_med_target))
                return xs
    raise ValueError(
        'Could not find cross section for m_med = {0} in {1}'
        .format(m_med_target, file)
        )


def get_model_name_from_tarball(tarball):
    match = re.search(r'(.*)_slc[67]', osp.basename(tarball))
    if not match:
        raise ValueError(
            'Could not determine model_name from {0}'
            .format(tarball)
            )
    model_name = match.group(1)
    logger.info('Retrieved model_name {0} from {1}'.format(model_name, tarball))
    return model_name


def get_mg_crosssection_from_logfile(log_file):
    """
    Gets the madgraph cross section from the log file that was created when creating a gridpack
    """
    with open(log_file) as f:
        match = re.search(r'(?<=Cross-section :   )(\d*.\d+)', f.read())
        if not match:
            raise ValueError(
                'Could not determine cross section from log_file {0}'.format(log_file)
                )
    xs = match.group(1)
    logger.info('Found cross section %s from log_file %s', xs, log_file)
    return float(xs)


def copy_to_output(file, change_name=None, dry=False):
    """
    Copies a file to the svj.genprod.SVJ_OUTPUT_DIR.
    Does not change the filename by default, but `change_name` can be passed
    to change the filename. The output directory will still be svj.genprod.SVJ_OUTPUT_DIR.
    """
    svj.core.utils.create_directory(svj.genprod.SVJ_OUTPUT_DIR)
    dst = osp.join(svj.genprod.SVJ_OUTPUT_DIR, osp.basename(file if change_name is None else change_name))
    logger.info('Copying {0} ==> {1}'.format(file, dst))
    if not dry:
        shutil.copyfile(file, dst)

