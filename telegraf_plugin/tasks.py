########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
########

import os
import sys
import shlex
import subprocess
import pkg_resources

from serv.serv import Serv, logger

import jinja2
import distro
import requests

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

import telegraf_plugin


@operation
def install(telegraf_config_inputs, telegraf_config_file='',
            telegraf_install_path='', download_url='', **kwargs):
    """Installation operation.

    Downloading and installing telegraf packacge - default version is 0.12.0.
    Default installation dir is set to /opt/telegraf.
    Only linux distributions are supported.
    """
    if 'linux' not in sys.platform:
        raise exceptions.NonRecoverableError('''Error!
         Telegraf-plugin is available on linux distribution only''')
    dist = distro.id()

    if not telegraf_install_path:
        telegraf_install_path = '/opt/telegraf'
    ctx.instance.runtime_properties[
        'telegraf_install_path'] = telegraf_install_path
    if os.path.isfile(telegraf_install_path):
        raise exceptions.NonRecoverableError(
            "Error! /opt/telegraf file already exists, can't create dir.")

    if not os.path.exists(telegraf_install_path):
        _run('sudo mkdir -p {0}'.format(telegraf_install_path))

    installation_file = download_telegraf(
        telegraf_install_path, dist, download_url)
    install_telegraf(telegraf_install_path, dist, installation_file)
    configure(telegraf_config_inputs, telegraf_config_file)


@operation
def start(telegraf_config_file='', **kwargs):
    """Start operation call for telegraf service,
    with telegraf_plugin configuration file.

    If telegraf service was already running -
    it will restart it and will use updated configuration file.
    """
    ctx.logger.info('Starting telegraf service...')
    if not telegraf_config_file:
        telegraf_config_file = '/etc/telegraf/telegraf.conf'
    if not os.path.isfile(telegraf_config_file):
        raise exceptions.NonRecoverableError("Config file doesn't exists")

    _run('sudo service telegraf restart')
    # logger.configure()
    # Serv().generate('/usr/lib/telegraf/scripts/telegraf.service', name='telegraf',
    #                 deploy=True, start=True, var='')
    ctx.logger.info(
        'GoodLuck! Telegraf service is up!'
        'Have an awesome monitoring experience...')


def download_telegraf(telegraf_install_path, dist, download_url='', **kwargs):
    """Downloading telegraf package form your desire url.

    Default url set to be version 0.12.0
    anf downloaded from official influxdb site.
    """
    ctx.logger.info('Downloading telegraf...')

    if not download_url:
        if dist in ('ubuntu', 'debian'):
            download_url = 'http://get.influxdb.org/telegraf/telegraf_0.12.0-1_amd64.deb'
        elif dist in ('centos', 'redhat'):
            download_url = 'http://get.influxdb.org/telegraf/telegraf-0.12.0-1.x86_64.rpm'
        else:
            raise exceptions.NonRecoverableError(
                'Error! distribution is not supported')
    installation_file = _download_file(download_url, telegraf_install_path)

    ctx.logger.info('Telegraf downloaded...installing..')
    return installation_file


def install_telegraf(telegraf_install_path, dist, installation_file, **kwargs):
    """Depacking telegraf package."""
    ctx.logger.info('Installing telegraf...')

    if dist in ('ubuntu', 'debian'):
        cmd = 'sudo dpkg -i {0}/{1}'.format(
            telegraf_install_path, installation_file)
    elif dist in ('centos', 'redhat'):
        cmd = 'sudo yum localinstall {0}/{1}'.format(
            telegraf_install_path, installation_file)
    else:
        raise exceptions.NonRecoverableError(
            'Error! distribution is not supported')
    _run(cmd)
    ctx.logger.info('Telegraf service was installed...')


def configure(telgraf_config, telegraf_config_file='', **kwargs):
    """Generating configuration file from your own desire destination
    or from telegraf_plugin telegraf.conf file.

    Rendering your inputs/outputs definitions.
    """
    ctx.logger.info('Configuring telegraf.conf...')

    if not telegraf_config_file:
        telegraf_config_file_temp = pkg_resources.resource_string(
            telegraf_plugin.__name__, 'resources/telegraf.conf')
        configuration = jinja2.Template(telegraf_config_file_temp)
        telegraf_config_file = '/tmp/telegraf.conf'
        with open(telegraf_config_file, 'w') as f:
            f.write(configuration.render(telgraf_config))
    else:
        ctx.download_resource_and_render(telegraf_config_file,
                                         template_variables=telgraf_config)
    _run('sudo mv {0} /etc/telegraf/telegraf.conf'.format(telegraf_config_file))
    ctx.logger.info('telegraf.conf was configured...')


def _download_file(url, destination):
    filename = url.split('/')[-1]
    temp_dir = '/tmp'
    local_filename = os.path.join(temp_dir, filename)
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as temp_file:
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                temp_file.write(chunk)
    _run('sudo mv {0} {1}'.format(local_filename, os.path.join(destination, filename)))
    return filename


def _run(command, retries=0, ignore_failures=False):
    if isinstance(command, str):
        command = shlex.split(command)
    stderr = subprocess.PIPE
    stdout = subprocess.PIPE

    ctx.logger.debug('Running: {0}'.format(command))
    proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    proc.aggr_stdout, proc.aggr_stderr = proc.communicate()
    if proc.returncode != 0:
        command_str = ' '.join(command)
        if retries:
            ctx.logger.warn('Failed running command: {0}. Retrying. '
                            '({1} left)'.format(command_str, retries))
            proc = _run(command, retries - 1)
        elif not ignore_failures:
            ctx.logger.error('Failed running command: {0} ({1}).'.format(
                command_str, proc.aggr_stderr))
            sys.exit(1)
    return proc
