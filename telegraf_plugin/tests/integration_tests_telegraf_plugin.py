########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


import os
import shutil
import unittest
import tempfile
import subprocess

import distro
from mock import patch

from cloudify.mocks import MockCloudifyContext
from .. import tasks


distro = distro.id()
PATH = os.path.dirname(__file__)
TEMP_TELEGRAF = os.path.join(tempfile.gettempdir(), 'telegraf')
CONFIG_FILE = os.path.join(TEMP_TELEGRAF, 'telegraf.conf')


def mock_install_ctx():
    return MockCloudifyContext()


def mock_get_resource_from_manager(resource_path):
    with open(resource_path) as f:
        return f.read()


class TesttelegrafPlugin(unittest.TestCase):

    def tearDown(self):
        # remove telegraf temp dir
        if os.path.exists(TEMP_TELEGRAF):
            shutil.rmtree(TEMP_TELEGRAF)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_install_service(self):
        '''verify service is available after installation -
         installation file is provided'''
        os.mkdir(TEMP_TELEGRAF)

        if distro in ('ubuntu', 'debian'):
            tasks.install_telegraf('telegraf_0.12.0-1_amd64.deb', PATH)
            output = subprocess.check_output(['dpkg', '-l', 'telegraf'])
            self.assertIn('telegraf', output)
        elif distro in ('centos', 'redhat'):
            tasks.install_telegraf('telegraf-0.12.0-1.x86_64.rpm', PATH)
            output = subprocess.check_output(['rpm', '-qa'])
            self.assertIn('telegraf', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_configure_with_inputs_no_file(self, *args):
        '''validate configuration without file -
        rendered correctly and placed on the right place'''
        os.mkdir(TEMP_TELEGRAF)

        dict1_valid = {
            'inputs': {'mem': None,
                       'io': None,
                       'disk': None,
                       'system': None,
                       'swap': None,
                       'cpu': {'percpu': False,
                               'totalcpu': True,
                               'drop': ['cpu_time']},
                       },
            'outputs': {'influxdb':
                        {'urls': ['http://localhost:8086'],
                         'database': 'monitoring_telegraf'},
                        }
            }

        tasks.configure('', dict1_valid)
        self.assertTrue(os.path.exists(CONFIG_FILE))
        output = subprocess.check_output(['telegraf',
                                          '-config',
                                          CONFIG_FILE,
                                          '-test'])
        self.assertNotIn('Error', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_failed_configure(self, *args):

        os.mkdir(TEMP_TELEGRAF)
        dict2_unvalid = {
            'inputs': None,
            'outputs': {'a': {'string': 'string'},
                        'b': None,
                        'c': {'list': ['a', 'b', 'c']}},
            'paths': {'a': {'string': 'string'},
                      'b': {'int': 10},
                      'c': {'list': None}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict2_unvalid)

        dict3_unvalid = {
            'inputs': {'a': None, 'b': {'int': 10},
                       'c': {'list': ['a', 'b', 'c']}},
            'outputs': None,
            'paths': {'a': {'string': 'string'}, 'b': None,
                      'c': {'list': ['a', 'b', 'c']}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict3_unvalid)

        dict4_unvalid = {
            'inputs': {'string': 'string', 'int': None,
                       'list': ['a', 'b', 'c']},
            'outputs': {'a': {'string': None},
                        'b': {'int': 10, 'list': ['a', 'b', 'c']}},
            'paths': '',
        }
        self.assertRaises(ValueError, tasks.configure, '', dict4_unvalid)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_get_resource_from_manager(os.path.join(
               'telegraf_plugin', 'tests', 'example_with_inputs.conf')))
    def test_configure_with_inputs_and_file(self, *args):
        '''validate configuration with inputs and file
         rendered correctly and placed on the right place'''
        os.mkdir(TEMP_TELEGRAF)

        dict1_valid = {
            'inputs': {'mem': None,
                       'io': None,
                       'disk': None,
                       'system': None,
                       'swap': None,
                       'cpu': {'percpu': False,
                               'totalcpu': True,
                               'drop': ['cpu_time']},
                       },
            'outputs': {'influxdb':
                        {'urls': ['http://localhost:8086'],
                         'database': 'monitoring_telegraf'},
                        }
        }

        tasks.configure(os.path.join('telegraf_plugin',
                                     'tests',
                                     'example_with_inputs.conf'), dict1_valid)
        self.assertTrue(os.path.exists(CONFIG_FILE))

        output = subprocess.check_output(['telegraf',
                                          '-config',
                                          CONFIG_FILE,
                                          '-test'])
        self.assertNotIn('Error', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_get_resource_from_manager(
               os.path.join('telegraf_plugin', 'tests', 'example.conf')))
    def test_configure_with_file_without_inputs(self, *args):
        '''validate configuration with file without inputs
         rendered correctly and placed on the right place'''
        os.mkdir(TEMP_TELEGRAF)

        tasks.configure(os.path.join(
            'telegraf_plugin', 'tests', 'example.conf'), None)
        self.assertTrue(os.path.exists(CONFIG_FILE))

        output = subprocess.check_output(['telegraf',
                                          '-config',
                                          CONFIG_FILE,
                                          '-test'])
        self.assertNotIn('Error', output)
