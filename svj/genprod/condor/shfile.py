#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp
import logging, os, collections
import svj.genprod
logger = logging.getLogger('root')


class SHBase(object):
    """docstring for SHBase"""
    def __init__(self):
        super(SHBase, self).__init__()

    def to_file(self, file, dry=False):
        parsed = self.parse()
        logger.info('Writing to {0}'.format(file))
        if not dry:
            with open(file, 'w') as f:
                f.write(parsed)


class SHClean(SHBase):
    """docstring for SHClean"""
    def __init__(self):
        super(SHClean, self).__init__()
        self.lines = [
            'rm *.stdout    > /dev/null 2>& 1'
            'rm *.stderr    > /dev/null 2>& 1'
            'rm *.log       > /dev/null 2>& 1'
            'rm docker_stderror > /dev/null 2>& 1'
            ]

    def parse(self):
        return '\n'.join(self.lines)


class SHStandard(SHBase):
    """docstring for SHStandard"""
    def __init__(self, python_file, svjgenprod_tarball=None):
        super(SHStandard, self).__init__()
        self.python_file = python_file

        self.repo_from_tarball = False
        if not(svjgenprod_tarball is None):
            self.repo_from_tarball = True
            self.svjgenprod_tarball = svjgenprod_tarball

        self.code_tarballs = []


    def add_code_tarball(self, code_tarball):
        self.code_tarballs.append(code_tarball)


    def clone(self):
        if self.repo_from_tarball: return self.clone_nogit()
        return [ 'git clone https://github.com/tklijnsma/svj.genprod.git' ]


    def clone_nogit(self):
        """
        No git available on LPC worker nodes;
        extract a provided tarball manually instead.
        Effectively git clone https://github.com/tklijnsma/svj.genprod.git
        """
        sh = [
            'mkdir svj.genprod',
            'tar xf svj.genprod.tar -C svj.genprod/',
            ]
        return sh


    def install(self):
        if self.repo_from_tarball: return self.install_nopip()
        return [ 'pip install --user -e svj.genprod' ]


    def install_nopip(self):
        """
        No pip available on LPC worker nodes;
        install package manually instead.
        Effectively pip install --user -e svj.genprod
        """        
        sh = [
            'export PATH="${PWD}/svj.genprod/bin:${PATH}"',
            'export PYTHONPATH="${PWD}/svj.genprod:${PYTHONPATH}"',
            ]
        return sh


    def install_code_tarballs(self):
        def code_tarball_iterator(code_tarballs):
            for tarball in code_tarballs:
                tarball = osp.basename(tarball)
                name = tarball.split('.')[0]
                yield tarball, name

        sh = []
        # First untar all tarballs
        for tarball, name in code_tarball_iterator(self.code_tarballs):
            sh.extend([
                'mkdir {0}'.format(name),
                'tar xf {0} -C {1}'.format(tarball, name),
                ])
        # Source the env script
        sh.append('source svj-core/env.sh')
        # Add the package paths
        for tarball, name in code_tarball_iterator(self.code_tarballs):
            sh.extend([
                'export PATH="${{PWD}}/svj/{0}/bin:${{PATH}}"'.format(name),
                'export PYTHONPATH="${{PWD}}/{0}:${{PYTHONPATH}}"'.format(name),
                ])
        return sh


    def parse(self):
        sh = []
        echo = lambda text: sh.append('echo "{0}"'.format(text))

        sh.append('#!/bin/bash')
        sh.append('set -e')
        echo('##### HOST DETAILS #####')
        echo('hostname: $(hostname)')
        echo('date:     $(date)')
        echo('pwd:      $(pwd)')
        sh.append('export SVJ_SEED=$1')
        echo('seed:     ${SVJ_SEED}')

        sh.extend(self.install_code_tarballs())

        sh.append('mkdir output')
        echo('ls -al:')
        sh.append('ls -al')

        echo('Starting python {0}'.format(osp.basename(self.python_file)))
        sh.append('python {0}'.format(osp.basename(self.python_file)))

        sh = '\n'.join(sh)
        logger.info('Parsed sh file:\n{0}'.format(sh))
        return sh








