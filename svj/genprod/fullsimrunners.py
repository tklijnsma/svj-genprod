#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os, shutil, sys, glob, subprocess, re, logging
import os.path as osp
from time import strftime

import svj.genprod
logger = logging.getLogger('root')
from . import FullSimRunnerBase

#____________________________________________________________________
class FullSimRunnerGenSim(FullSimRunnerBase):
    """docstring for FullSimRunnerGenSim"""

    stage = 'gensim'
    substage = 'GEN_SIM'

    @classmethod
    def subclass_per_year(cls):
        return {
            2016: FullSimRunnerGenSim2016,
            2017: FullSimRunnerGenSim2017,
            2018: FullSimRunnerGenSim2018,
            }

    def __init__(self, *args, **kwargs):
        super(FullSimRunnerGenSim, self).__init__(*args, **kwargs)
        self.gensimfragment_basename = 'SVJGenSimFragment.py'
        self.gensimfragment_dir = osp.join(self.get_cmssw_src(), 'Configuration/GenProduction/python')
        self.gensimfragment_file = osp.join(self.gensimfragment_dir, self.gensimfragment_basename)

    def full_chain(self):
        self.setup_cmssw()
        self.add_gensimfragment()
        self.cmsdriver()
        self.edit_cmsdriver_output()
        self.edit_cmsdriver_rnd_service()
        self.cmsrun()

    def add_gensimfragment(self):
        """
        Creates the gensimfragment
        """
        svj.core.utils.create_directory(self.gensimfragment_dir)
        gensimfragment = svj.genprod.GenSimFragment(self.config)
        gensimfragment.to_file(self.gensimfragment_file)
        self.compile_cmssw()

    def edit_cmsdriver_output(self):
        """
        Takes the cfg file generated by cmsDriver.py, edits some lines, and re-saves
        Based on simple string replacement, somewhat fragile code
        """
        logger.warning('Doing dangerous replacements on {0}; fragile code!'.format(self.cfg_file))

        contents = self._get_cmsdriver_output()

        def replace_exactly_once(string, to_replace, replace_by):
            if not to_replace in string:
                raise ValueError('Substring "{0}" not found'.format(string))
            return string.replace(to_replace, replace_by, 1)

        # Add to CMSSW config in case stringent hadronisation cuts remove all events from a job
        contents = replace_exactly_once(contents,
            'process.options = cms.untracked.PSet(\n',
            ( 
                'process.options = cms.untracked.PSet(\n'
                '    SkipEvent = cms.untracked.vstring(\'ProductNotFound\'),\n'
                )
            )

        # Add to CMSSW config to ensure Z2 and dark quark filters are used
        contents = replace_exactly_once(contents,
            'seq = process.generator',
            'seq = (process.generator + process.darkhadronZ2filter + process.darkquarkFilter)'
            )

        logger.warning('EXTREMELY FRAGILE: Editing %s to keep gen jets', self.cfg_file)
        contents += (
            '\n\nfor particle in ["genParticlesForJetsNoMuNoNu","genParticlesForJetsNoNu","genCandidatesForMET","genParticlesForMETAllVisible"]:\n'
            '    if hasattr(process, particle): getattr(process, particle).ignoreParticleIDs.extend([51,52,53])\n'
            'if hasattr(process,"recoGenJets") and hasattr(process,"recoAllGenJetsNoNu"):\n'
            '    process.recoGenJets += process.recoAllGenJetsNoNu\n'
            'if hasattr(process,\'genJetParticles\') and hasattr(process,\'genParticlesForJetsNoNu\'):\n'
            '    process.genJetParticles += process.genParticlesForJetsNoNu\n'
            '    process.RAWSIMEventContent.outputCommands.extend([\n'
            '        \'keep *_genParticlesForJets_*_*\',\n'
            '        \'keep *_genParticlesForJetsNoNu_*_*\',\n'
            '        ])\n'
            )

        self._overwrite_cmsdriver_output(contents)


class FullSimRunnerGenSim2016(FullSimRunnerGenSim):
    # earlier versions don't have CMSSW plug-ins for dark quark/Z2 filters
    cmssw_version = 'CMSSW_7_1_38_patch1'
    arch = 'slc6_amd64_gcc481'
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

class FullSimRunnerGenSim2017(FullSimRunnerGenSim):
    # earlier versions (at least <=9_3_12) don't have CMSSW plug-ins for dark quark/Z2 filters
    cmssw_version = 'CMSSW_9_3_15'
    arch = 'slc7_amd64_gcc630'
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py Configuration/GenProduction/python/{0}'.format(self.gensimfragment_basename),
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--mc',
            '--eventcontent RAWSIM',
            '--datatier GEN-SIM',
            '--conditions 93X_mc2017_realistic_v3',
            '--beamspot Realistic25ns13TeVEarly2017Collision',
            '--step GEN,SIM',
            '--geometry DB:Extended',
            '--era Run2_2017',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

class FullSimRunnerGenSim2018(FullSimRunnerGenSim):
    # earlier versions (at least <=10_2_3) don't have CMSSW plug-ins for dark quark/Z2 filters
    cmssw_version = 'CMSSW_10_2_15'
    arch = 'slc7_amd64_gcc700'
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py Configuration/GenProduction/python/{0}'.format(self.gensimfragment_basename),
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--mc',
            '--eventcontent RAWSIM',
            '--datatier GEN-SIM',
            '--conditions 102X_upgrade2018_realistic_v11',
            '--beamspot Realistic25ns13TeVEarly2018Collision',
            '--step GEN,SIM',
            '--geometry DB:Extended',
            '--era Run2_2018',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]


#____________________________________________________________________
class FullSimRunnerGen(FullSimRunnerGenSim):
    """
    Simplification of the GEN-SIM step, without the SIM part.
    """
    stage = 'gen'
    substage = 'GEN'

    @classmethod
    def subclass_per_year(cls):
        return {
            2016: FullSimRunnerGen2016,
            2017: FullSimRunnerGen2017,
            2018: FullSimRunnerGen2018,
            }

class FullSimRunnerGen2016(FullSimRunnerGen):
    # earlier versions don't have CMSSW plug-ins for dark quark/Z2 filters
    cmssw_version = 'CMSSW_7_1_38_patch1'
    arch = 'slc6_amd64_gcc481'
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

class FullSimRunnerGen2017(FullSimRunnerGen):
    # earlier versions (at least <=9_3_12) don't have CMSSW plug-ins for dark quark/Z2 filters
    cmssw_version = 'CMSSW_9_3_15'
    arch = 'slc7_amd64_gcc630'
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py Configuration/GenProduction/python/{0}'.format(self.gensimfragment_basename),
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--mc',
            '--eventcontent RAWSIM',
            '--datatier GEN',
            '--conditions 93X_mc2017_realistic_v3',
            '--beamspot Realistic25ns13TeVEarly2017Collision',
            '--step GEN',
            # '--geometry DB:Extended',
            '--era Run2_2017',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

class FullSimRunnerGen2018(FullSimRunnerGen):
    # earlier versions (at least <=10_2_3) don't have CMSSW plug-ins for dark quark/Z2 filters
    cmssw_version = 'CMSSW_10_2_15'
    arch = 'slc7_amd64_gcc700'
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py Configuration/GenProduction/python/{0}'.format(self.gensimfragment_basename),
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--mc',
            '--eventcontent RAWSIM',
            '--datatier GEN',
            '--conditions 102X_upgrade2018_realistic_v11',
            '--beamspot Realistic25ns13TeVEarly2018Collision',
            '--step GEN',
            # '--geometry DB:Extended',
            '--era Run2_2018',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

#____________________________________________________________________
aod_cmssw_version_2016 = 'CMSSW_8_0_21'
aod_arch_2016 = 'slc6_amd64_gcc530'

aod_cmssw_version_2017 = 'CMSSW_9_4_10'
aod_arch_2017 = 'slc7_amd64_gcc630'

aod_cmssw_version_2018 = 'CMSSW_10_2_15'
aod_arch_2018 = 'slc7_amd64_gcc700'


class FullSimRunnerAOD(FullSimRunnerBase):
    stage = 'aod'
    substage = 'AOD_step1'
    @classmethod
    def subclass_per_year(cls):
        return {
        2016: FullSimRunnerAOD2016,
        2017: FullSimRunnerAOD2017,
        2018: FullSimRunnerAOD2018,
        }

    def full_chain(self):
        self.setup_cmssw()
        self.copy_pileup_filelist()
        self.cmsdriver()
        self.edit_cmsdriver_rnd_service()
        self.cmsrun()


class FullSimRunnerAOD2016(FullSimRunnerAOD):
    cmssw_version = aod_cmssw_version_2016
    arch = aod_arch_2016
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

class FullSimRunnerAOD2017(FullSimRunnerAOD):
    cmssw_version = aod_cmssw_version_2017
    arch = aod_arch_2017
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py step1',
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--pileup_input filelist:"{0}"'.format(osp.join(self.workdir, self.pileup_filelist_basename)),
            '--mc',
            '--eventcontent PREMIXRAW',
            '--datatier GEN-SIM-RAW',
            '--conditions 94X_mc2017_realistic_v11',
            '--step DIGIPREMIX_S2,DATAMIX,L1,DIGI2RAW,HLT:2e34v40',
            '--datamix PreMix',
            '--era Run2_2017',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

class FullSimRunnerAOD2018(FullSimRunnerAOD):
    cmssw_version = aod_cmssw_version_2018
    arch = aod_arch_2018
    def get_cmsdriver_cmd(self):
        raise NotImplementedError


#____________________________________________________________________
class FullSimRunnerAODstep2(FullSimRunnerBase):
    stage = 'aod'
    substage = 'AOD_step2'
    @classmethod
    def subclass_per_year(cls):
        return {
        2016: FullSimRunnerAODstep22016,
        2017: FullSimRunnerAODstep22017,
        2018: FullSimRunnerAODstep22018,
        }

class FullSimRunnerAODstep22016(FullSimRunnerAODstep2):
    cmssw_version = aod_cmssw_version_2016
    arch = aod_arch_2016
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

class FullSimRunnerAODstep22017(FullSimRunnerAODstep2):
    cmssw_version = aod_cmssw_version_2017
    arch = aod_arch_2017
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py step2',
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file),
            '--mc',
            '--eventcontent AODSIM',
            '--runUnscheduled',
            '--datatier AODSIM',
            '--conditions 94X_mc2017_realistic_v11',
            '--step RAW2DIGI,RECO,RECOSIM,EI',
            '--era Run2_2017',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

class FullSimRunnerAODstep22018(FullSimRunnerAODstep2):
    cmssw_version = aod_cmssw_version_2018
    arch = aod_arch_2018
    def get_cmsdriver_cmd(self):
        raise NotImplementedError


#____________________________________________________________________
class FullSimRunnerMiniAOD(FullSimRunnerBase):
    stage = 'aod'
    substage = 'MiniAOD'
    @classmethod
    def subclass_per_year(cls):
        return {
        2016: FullSimRunnerMiniAOD2016,
        2017: FullSimRunnerMiniAOD2017,
        2018: FullSimRunnerMiniAOD2018,
        }

class FullSimRunnerMiniAOD2016(FullSimRunnerMiniAOD):
    cmssw_version = aod_cmssw_version_2016
    arch = aod_arch_2016
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

class FullSimRunnerMiniAOD2017(FullSimRunnerMiniAOD):
    cmssw_version = aod_cmssw_version_2017
    arch = aod_arch_2017
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py',
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--mc',
            '--eventcontent MINIAODSIM',
            '--runUnscheduled',
            '--datatier MINIAODSIM',
            '--conditions 94X_mc2017_realistic_v14',
            '--step PAT',
            '--scenario pp',
            '--era Run2_2017,run2_miniAOD_94XFall17',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

class FullSimRunnerMiniAOD2018(FullSimRunnerMiniAOD):
    cmssw_version = aod_cmssw_version_2018
    arch = aod_arch_2018
    def get_cmsdriver_cmd(self):
        raise NotImplementedError


#____________________________________________________________________
class FullSimRunnerNanoAOD(FullSimRunnerBase):
    stage = 'nano'
    substage = 'NanoAOD'
    @classmethod
    def subclass_per_year(cls):
        return {
        2016: FullSimRunnerNanoAOD2016,
        2017: FullSimRunnerNanoAOD2017,
        2018: FullSimRunnerNanoAOD2018,
        }

    def edit_cmsdriver_output(self):
        """
        Takes the cfg file generated by cmsDriver.py, edits some lines, and re-saves
        Based on simple string replacement, somewhat fragile code
        """
        logger.warning('Changing default NanoAOD sequence to omit the RivetProducer')
        contents = self._get_cmsdriver_output()
        contents += '\n'.join([
            '\n\n# EDITTED FOR SVJ: Change default NanoAOD sequence to skip the RivetProducer',
            'process.particleLevelSequence = cms.Sequence(',
            '    process.mergedGenParticles',
            '    + process.genParticles2HepMC',
            '    + process.particleLevel',
            '    + process.tautagger',
            '    + process.genParticles2HepMCHiggsVtx',
            '    )',
            'process.particleLevelTables = cms.Sequence(process.rivetLeptonTable + process.rivetMetTable)',
            ])
        self._overwrite_cmsdriver_output(contents)

class FullSimRunnerNanoAOD2016(FullSimRunnerNanoAOD):
    cmssw_version = 'CMSSW_9_4_4'
    arch = 'slc6_amd64_gcc630'
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

class FullSimRunnerNanoAOD2017(FullSimRunnerNanoAOD):
    cmssw_version = 'CMSSW_10_2_15'
    arch = 'slc7_amd64_gcc700'
    def get_cmsdriver_cmd(self):
        return [
            'cmsDriver.py',
            '--filein file:{0}'.format(self.in_file),
            '--fileout file:{0}'.format(self.out_root_file_basename),
            '--mc',
            '--eventcontent NANOAODSIM',
            '--datatier NANOAODSIM',
            '--conditions 102X_mc2017_realistic_v7',
            '--step NANO',
            '--era Run2_2017,run2_nanoAOD_94XMiniAODv2',
            '--customise Configuration/DataProcessing/Utils.addMonitoring',
            '--python_filename {0}'.format(self.cfg_file_basename),
            '--no_exec',
            '-n {0}'.format(self.n_events),
            ]

class FullSimRunnerNanoAOD2018(FullSimRunnerNanoAOD):
    cmssw_version = 'CMSSW_10_2_15'
    arch = 'slc7_amd64_gcc700'
    def get_cmsdriver_cmd(self):
        raise NotImplementedError

