# -*- coding: utf-8 -*-
#
# 2011-2013 Steven Armstrong (steven-cdist at armstrong.cc)
# 2011-2013 Nico Schottelius (nico-cdist at schottelius.org)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

import logging
import os

import cdist
from . import util

'''
common:
    runs only locally, does not need remote

    env:
        PATH: prepend directory with type emulator symlinks == local.bin_path
        __target_host: the target host we are working on
        __target_hostname: the target hostname provided from __target_host
        __target_fqdn: the target's fully qualified domain name provided from
                       __target_host
        __global: full qualified path to the global
                  output dir == local.out_path
        __cdist_manifest: full qualified path of the manifest == script
        __cdist_type_base_path: full qualified path to the directory where
                                types are defined for use in type emulator
            == local.type_path
        __files: full qualified path to the files dir
        __target_host_tags: comma spearated list of host tags

initial manifest is:
    script: full qualified path to the initial manifest

    env:
        __manifest: path to .../conf/manifest/ == local.manifest_path

    creates: new objects through type emulator

type manifeste is:
    script: full qualified path to the type manifest

    env:
        __object: full qualified path to the object's dir
        __object_id: the objects id
        __object_fq: full qualified object id, iow: $type.name + / + object_id
        __type: full qualified path to the type's dir

    creates: new objects through type emulator
'''


class NoInitialManifestError(cdist.Error):
    """
    Display missing initial manifest:
        - Display path if user given
            - try to resolve link if it is a link
        - Omit path if default (is a linked path in temp directory without
            much help)
    """

    def __init__(self, manifest_path, user_supplied):
        msg_header = "Initial manifest missing"

        if user_supplied:
            if os.path.islink(manifest_path):
                self.message = "{}: {} -> {}".format(
                    msg_header, manifest_path, os.path.realpath(manifest_path))
            else:
                self.message = "{}: {}".format(msg_header, manifest_path)
        else:
            self.message = "{}".format(msg_header)

    def __str__(self):
        return repr(self.message)


class Manifest:
    """Executes cdist manifests.

    """

    ORDER_DEP_STATE_NAME = 'order_dep_state'
    TYPEORDER_DEP_NAME = 'typeorder_dep'

    def __init__(self, target_host, local, dry_run=False):
        self.target_host = target_host
        self.local = local

        self._open_logger()

        self.env = {
            'PATH': "{}:{}".format(self.local.bin_path, os.environ['PATH']),
            # for use in type emulator
            '__cdist_type_base_path': self.local.type_path,
            '__global': self.local.base_path,
            '__target_host': self.target_host[0],
            '__target_hostname': self.target_host[1],
            '__target_fqdn': self.target_host[2],
            '__files': self.local.files_path,
            '__target_host_tags': self.local.target_host_tags,
            '__cdist_log_level': util.log_level_env_var_val(self.log),
            '__cdist_log_level_name': util.log_level_name_env_var_val(
                self.log),
            '__cdist_colored_log': str(
                cdist.log.CdistFormatter.USE_COLORS).lower(),
        }

        if dry_run:
            self.env['__cdist_dry_run'] = '1'

    def _open_logger(self):
        self.log = logging.getLogger(self.target_host[0])

    # logger is not pickable, so remove it when we pickle
    def __getstate__(self):
        state = self.__dict__.copy()
        if 'log' in state:
            del state['log']
        return state

    # recreate logger when we unpickle
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._open_logger()

    def env_initial_manifest(self, initial_manifest):
        env = os.environ.copy()
        env.update(self.env)
        env['__cdist_manifest'] = initial_manifest
        env['__manifest'] = self.local.manifest_path
        env['__explorer'] = self.local.global_explorer_out_path

        return env

    def run_initial_manifest(self, initial_manifest=None):
        if not initial_manifest:
            initial_manifest = self.local.initial_manifest
            user_supplied = False
        else:
            user_supplied = True

        if not os.path.isfile(initial_manifest):
            raise NoInitialManifestError(initial_manifest, user_supplied)

        message_prefix = "initialmanifest"
        self.log.verbose("Running initial manifest %s", initial_manifest)
        which = "init"
        if self.local.save_output_streams:
            stderr_path = os.path.join(self.local.stderr_base_path, which)
            stdout_path = os.path.join(self.local.stdout_base_path, which)
            with open(stderr_path, 'ba+') as stderr, \
                    open(stdout_path, 'ba+') as stdout:
                self.local.run_script(
                    initial_manifest,
                    env=self.env_initial_manifest(initial_manifest),
                    message_prefix=message_prefix,
                    stdout=stdout, stderr=stderr)
        else:
            self.local.run_script(
                initial_manifest,
                env=self.env_initial_manifest(initial_manifest),
                message_prefix=message_prefix)

    def env_type_manifest(self, cdist_object):
        type_manifest = os.path.join(self.local.type_path,
                                     cdist_object.cdist_type.manifest_path)
        env = os.environ.copy()
        env.update(self.env)
        env.update({
            '__cdist_manifest': type_manifest,
            '__manifest': self.local.manifest_path,
            '__object': cdist_object.absolute_path,
            '__object_id': cdist_object.object_id,
            '__object_name': cdist_object.name,
            '__type': cdist_object.cdist_type.absolute_path,
        })

        return env

    def run_type_manifest(self, cdist_object):
        type_manifest = os.path.join(self.local.type_path,
                                     cdist_object.cdist_type.manifest_path)
        message_prefix = cdist_object.name
        which = 'manifest'
        if os.path.isfile(type_manifest):
            self.log.verbose("Running type manifest %s for object %s",
                             type_manifest, cdist_object.name)
            if self.local.save_output_streams:
                stderr_path = os.path.join(cdist_object.stderr_path, which)
                stdout_path = os.path.join(cdist_object.stdout_path, which)
                with open(stderr_path, 'ba+') as stderr, \
                        open(stdout_path, 'ba+') as stdout:
                    self.local.run_script(
                        type_manifest,
                        env=self.env_type_manifest(cdist_object),
                        message_prefix=message_prefix,
                        stdout=stdout, stderr=stderr)
            else:
                self.local.run_script(
                    type_manifest,
                    env=self.env_type_manifest(cdist_object),
                    message_prefix=message_prefix)

    def cleanup(self):
        def _rm_file(fname):
            try:
                self.log.trace("[ORDER_DEP] Removing %s", fname)
                os.remove(os.path.join(self.local.base_path, fname))
            except FileNotFoundError:
                pass
        _rm_file(Manifest.ORDER_DEP_STATE_NAME)
        _rm_file(Manifest.TYPEORDER_DEP_NAME)
