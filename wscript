#!/usr/bin/env python
import os
import re
import shutil
import waflib.extras.autowaf as autowaf

MDA_VERSION = '1.0.0'

# Mandatory waf variables
APPNAME = 'MDA'        # Package name for waf dist
VERSION = MDA_VERSION  # Package version for waf dist
top     = '.'          # Source directory
out     = 'build'      # Build directory

def options(opt):
    opt.load('compiler_cxx')
    autowaf.set_options(opt)

def configure(conf):
    conf.load('compiler_cxx')
    autowaf.configure(conf)
    conf.line_just = 23
    autowaf.display_header('MDA.lv2 Configuration')

    autowaf.check_pkg(conf, 'lv2', atleast_version='1.0.0', uselib_store='LV2')

    autowaf.display_msg(conf, "LV2 bundle directory",
                        conf.env.LV2DIR)
    print('')

def build(bld):
    bundle = 'mda.lv2'

    # Copy data files to build bundle (build/mda.lv2)
    def do_copy(task):
        src = task.inputs[0].abspath()
        tgt = task.outputs[0].abspath()
        return shutil.copy(src, tgt)

    for i in bld.path.ant_glob('mda.lv2/[A-Z]*.ttl'):
        bld(rule   = do_copy,
            source = i,
            target = bld.path.get_bld().make_node('mda.lv2/%s' % i),
            install_path = '${LV2DIR}/mda.lv2')

    # Make a pattern for shared objects without the 'lib' prefix
    module_pat = re.sub('^lib', '', bld.env.cxxshlib_PATTERN)
    module_ext = module_pat[module_pat.rfind('.'):]

    # Build manifest by substitution
    bld(features     = 'subst',
        source       = 'mda.lv2/manifest.ttl.in',
        target       = bld.path.get_bld().make_node('mda.lv2/manifest.ttl'),
        LIB_EXT      = module_ext,
        install_path = '${LV2DIR}/mda.lv2')

    plugins = '''
            Ambience
            Bandisto
            BeatBox
            Combo
            DX10
            DeEss
            Degrade
            Delay
            Detune
            Dither
            DubDelay
            Dynamics
            EPiano
            Image
            JX10
            Leslie
            Limiter
            Loudness
            MultiBand
            Overdrive
            Piano
            RePsycho
            RezFilter
            RingMod
            RoundPan
            Shepard
            Splitter
            Stereo
            SubSynth
            TalkBox
            TestTone
            ThruZero
            Tracker
            Transient
            VocInput
            Vocoder
    '''.split()

    for p in plugins:
        # Build plugin library
        obj = bld(features     = 'cxx cxxshlib',
                  source       = ['src/mda%s.cpp' % p, 'lvz/wrapper.cpp'],
                  includes     = ['.', './lvz', './src'],
                  name         = p,
                  target       = os.path.join(bundle, p),
                  install_path = '${LV2DIR}/' + bundle,
                  uselib       = ['LV2'],
                  defines      = ['PLUGIN_CLASS=mda%s' % p,
                                  'URI_PREFIX="http://drobilla.net/plugins/mda/"',
                                  'PLUGIN_URI_SUFFIX="%s"' % p,
                                  'PLUGIN_HEADER="src/mda%s.h"' % p])
        obj.env.cxxshlib_PATTERN = module_pat

        # Install data file
        bld.install_files('${LV2DIR}/' + bundle, os.path.join(bundle, p + '.ttl'))
