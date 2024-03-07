# This is a copy of https://github.com/ansible-collections/community.general/blob/main/plugins/callback/log_plays.py
# But with these changes:
#  - Optionally use a new log file for each playbook run
#  - Added multi_line_yaml format to get more readable log files
#  - Drop stdout/err_lines if stdout/err is also present
#  - Omit internal data
#  - Respect _ansible_no_log
#
# The latter three (plus some the yaml Dumper class) were taken from
# https://github.com/ansible-collections/community.general/blob/main/plugins/callback/yaml.py
#
# TODO: Submit these changes back upstream
#
# -*- coding: utf-8 -*-
# Copyright (c) 2012, Michael DeHaan, <michael.dehaan@gmail.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author: Unknown (!UNKNOWN)
    name: log_plays
    type: notification
    short_description: write playbook output to log file
    description:
      - This callback writes playbook output to a file per host in the C(/var/log/ansible/hosts) directory.
    requirements:
     - Whitelist in configuration
     - A writeable C(/var/log/ansible/hosts) directory by the user executing Ansible on the controller
    options:
      log_folder:
        default: /var/log/ansible/hosts
        description: The folder where log files will be created.
        env:
          - name: ANSIBLE_LOG_FOLDER
        ini:
          - section: callback_log_plays
            key: log_folder
      log_format:
        default: single_line_json
        description: The format to use for log lines
        choices: [single_line_json, multi_line_yaml]
        env:
          - name: ANSIBLE_LOG_FORMAT
        ini:
          - section: callback_log_plays
            key: log_format
      log_file_per_playbook_run:
        default: false
        description: Whether to log each playbook run and host to its own file (true), or just have a single file per host (false)
        type: bool
        env:
          - name: ANSIBLE_LOG_FILE_PER_PLAYBOOK_RUN
        ini:
          - section: callback_log_plays
            key: log_file_per_playbook_run
'''

import os
import re
import time
import json
import yaml
import string

from ansible.utils.path import makedirs_safe
from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.callback import strip_internal_keys, module_response_deepcopy

# should_use_block and MyDumper copied from https://github.com/ansible-collections/community.general/blob/main/plugins/callback/yaml.py
def should_use_block(value):
    """Returns true if string should be in block format"""
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False

class MyDumper(AnsibleDumper):
    def represent_scalar(self, tag, value, style=None):
        """Uses block style for multi-line strings"""
        if style is None:
            if should_use_block(value):
                style = '|'
                # we care more about readable than accuracy, so...
                # ...no trailing space
                value = value.rstrip()
                # ...and non-printable characters
                value = ''.join(x for x in value if x in string.printable or ord(x) >= 0xA0)
                # ...tabs prevent blocks from expanding
                value = value.expandtabs()
                # ...and odd bits of whitespace
                value = re.sub(r'[\x0b\x0c\r]', '', value)
                # ...as does trailing space
                value = re.sub(r' +\n', '\n', value)
            else:
                style = self.default_style
        node = yaml.representer.ScalarNode(tag, value, style=style)
        if self.alias_key is not None:
            self.represented_objects[self.alias_key] = node
        return node

# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.


class CallbackModule(CallbackBase):
    """
    logs playbook results, per host, in /var/log/ansible/hosts
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'community.general.log_plays'
    CALLBACK_NEEDS_WHITELIST = True

    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    FILENAME_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
    MSG_FORMAT = "%(now)s - %(playbook)s - %(task_name)s - %(task_action)s - %(category)s - %(data)s\n\n"

    def __init__(self):

        super(CallbackModule, self).__init__()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.log_folder = self.get_option("log_folder")
        self.format = self.get_option("log_format")
        self.file_per_run = self.get_option("log_file_per_playbook_run")

        if not os.path.exists(self.log_folder):
            makedirs_safe(self.log_folder)

    def log(self, result, category):
        data = result._result
        if isinstance(data, MutableMapping):
            if '_ansible_verbose_override' in data:
                # avoid logging extraneous data
                data = 'omitted'
            elif data.get('_ansible_no_log', False):
                data = 'omitted due to no_log'
            else:
                data = strip_internal_keys(module_response_deepcopy(result._result))

                # if we already have stdout, we don't need stdout_lines
                if 'stdout' in data and 'stdout_lines' in data:
                    data['stdout_lines'] = '<omitted>'

                # if we already have stderr, we don't need stderr_lines
                if 'stderr' in data and 'stderr_lines' in data:
                    data['stderr_lines'] = 'omitted'

                if self.format == 'single_line_json':
                    invocation = data.pop('invocation', None)
                    data = json.dumps(data, cls=AnsibleJSONEncoder)
                    if invocation is not None:
                        data = json.dumps(invocation) + " => %s " % data
                else:
                    # This introduces an extra dict layer so all of the
                    # dict contents end up *after* the log line, and all
                    # lines are indented
                    data = yaml.dump({'result': data}, Dumper=MyDumper, default_flow_style=False)

        path = os.path.join(self.log_folder, self.filename_prefix + result._host.get_name())
        now = time.strftime(self.TIME_FORMAT, time.localtime())

        msg = to_bytes(
            self.MSG_FORMAT
            % dict(
                now=now,
                playbook=self.playbook,
                task_name=result._task.name,
                task_action=result._task.action,
                category=category,
                data=data,
            )
        )
        with open(path, "ab") as fd:
            fd.write(msg)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.log(result, 'FAILED')

    def v2_runner_on_ok(self, result):
        self.log(result, 'OK')

    def v2_runner_on_skipped(self, result):
        self.log(result, 'SKIPPED')

    def v2_runner_on_unreachable(self, result):
        self.log(result, 'UNREACHABLE')

    def v2_runner_on_async_failed(self, result):
        self.log(result, 'ASYNC_FAILED')

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook._file_name
        if self.file_per_run:
            self.filename_prefix = '{}-{}-'.format(time.strftime(self.FILENAME_TIME_FORMAT, time.localtime()), self.playbook)
        else:
            self.filename_prefix = ''

    def v2_playbook_on_import_for_host(self, result, imported_file):
        self.log(result, 'IMPORTED', imported_file)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        self.log(result, 'NOTIMPORTED', missing_file)
