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
            try:
                shutil.rmtree(TEMP_TELEGRAF)
            except:
                subprocess.call(['sudo', 'rm', '-rf', TEMP_TELEGRAF])

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_download_telegraf(self):
        '''test download_telegraf function'''
        os.mkdir(TEMP_TELEGRAF)

        filename = tasks.download_telegraf('', TEMP_TELEGRAF)
        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'telegraf_0.12.0-1_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'telegraf-0.12.0-1.x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_TELEGRAF, filename)))

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_download_telegraf_path_not_exists(self):
        '''test download - verify nothing downloaded'''
        filename = tasks.download_telegraf('', TEMP_TELEGRAF)

        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'telegraf_0.12.0-1_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'telegraf-0.12.0-1.x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_TELEGRAF, filename)))

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_download_file(self):
        '''test download -  verify file exists after download'''
        os.mkdir(TEMP_TELEGRAF)

        filename = tasks._download_file(
            'http://get.influxdb.org/telegraf/' +
            'telegraf_0.12.0-1_amd64.deb',
            TEMP_TELEGRAF)
        self.assertEqual(filename, 'telegraf_0.12.0-1_amd64.deb')
        self.assertTrue(os.path.exists(os.path.join(TEMP_TELEGRAF, filename)))

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', mock_install_ctx())
    def test_download_file_failed(self):
        '''test download - verify nothing downloaded'''
        os.mkdir(TEMP_TELEGRAF)

        self.assertRaises(ValueError, tasks._download_file, None, None)
