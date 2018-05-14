#
#    Copyright 2017 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

"""
Template system that uses courutines
"""
import asyncio
import os
import importlib

from jinja2 import Environment, FileSystemLoader


class TemplateSystem:
    """
    Extensible template system
    """

    def __init__(self, template_file, output_file, bash_command=None, signal=None, pid=None, pid_file=None):
        """
        Initialize template system

        :param template_file: source file
        :type template_file: str
        :param output_file: target file
        :type output_file: str
        :param bash_command: (Optional) bash command to execute on file render
        :type bash_command: str
        :param signal: (Optional) signal id, that is sent to a process on render
        :type signal: int
        :param pid: (Optional) process id, that receives signal on render
        :type pid: int
        :param pid_file: (Optional) process id file, that receives signal on render
        :type pid_file: str
        """
        self._template_file = template_file
        self._output_file = output_file
        self._bash_command = bash_command
        self._signal = signal
        self._pid = pid
        self._pid_file = pid_file

        if signal and type(signal) != int:
            raise ValueError('Signal value should be an integer')
        if pid and type(pid) != int:
            raise ValueError('PID value should be an integer')
        if signal and not pid and not pid_file:
            raise ValueError('PID or PID file parameters is required, if signal is specified')

        self._j2 = Environment(
            loader=FileSystemLoader(os.getcwd())
        )
        self._template = self._j2.get_template(template_file)

        self._context = {
            'load_module': self.load_module
        }
        self._loaded_modules = set()
        self._coroutines = []
        self._loop = asyncio.get_event_loop()

    def load_module(self, name, *args, **kwargs):
        """
        Load module
        Example: {{ load_module('loadable_module', 1) }}
        and module should be
            async def temp(template_system, *args, **kwargs):
                print("I'm in template extension")
                for i in range(2):
                    template_system.render(a=i)
                    await asyncio.sleep(1)

        :param name: name of module
        :type name: str
        :param args: additional positional arguments
        :type args: any
        :param kwargs: additional key-value arguments
        :type args: any
        :return: str -- empty string
        """
        if name in self._loaded_modules:
            return ''

        self._loaded_modules.add(name)

        module_name, function_name = name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        module_function = getattr(module, function_name)
        future = asyncio.ensure_future(module_function(self, *args, **kwargs))

        self._coroutines.append(future)
        return ''

    def render(self, **items):
        """
        Render template and execute bash commend, if specified

        :param items: values to update context
        :type items: dict[str, Any]
        :return: None
        """
        self._context.update(items)
        with open(self._output_file, 'w') as file_stream:
            file_stream.write(self._template.render(self._context))
            if self._bash_command:
                os.system(self._bash_command)
            if self._signal and self._pid:
                os.kill(self._pid, self._signal)
            if self._signal and self._pid_file:
                with open(self._pid_file) as pf:
                    os.kill(pf.read(), self._signal)

    def render_loop(self):
        """
        Start render loop

        :return: None
        """
        self.render()
        self._loop.run_until_complete(asyncio.wait(self._coroutines))
