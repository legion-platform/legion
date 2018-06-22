#
#    Copyright 2018 EPAM Systems
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
import logging
import os
import os.path
import importlib

import asyncio
from asyncio.tasks import Task

from jinja2 import Environment, FileSystemLoader, Undefined

LOGGER = logging.getLogger(__name__)


class LegionTemplateEngine:
    """
    Extensible template system
    """

    def __init__(self, template_file, output_file, command=None, signal=None, pid=None, pid_file=None):
        """
        Initialize template system

        :param template_file: source file
        :type template_file: str
        :param output_file: target file
        :type output_file: str
        :param command: (Optional) bash command to execute on file render
        :type command: str
        :param signal: (Optional) signal id, that is sent to a process on render
        :type signal: int
        :param pid: (Optional) process id, that receives signal on render
        :type pid: int
        :param pid_file: (Optional) process id file, that receives signal on render
        :type pid_file: str
        """
        LOGGER.debug('Creating LegionTemplateEngine instance for source={}, destination={}'
                     .format(template_file, output_file))
        self._template_file = template_file
        self._output_file = output_file
        self._command = command
        self._signal = signal
        self._pid = pid
        self._pid_file = pid_file

        if signal and not pid and not pid_file:
            raise ValueError('PID or PID file parameters is required, if signal is specified')

        self._j2 = Environment(
            loader=FileSystemLoader([os.getcwd(), '/']),
            undefined=SilentUndefined
        )
        self._template = self._j2.get_template(template_file)

        self._context = {
            'load_module': self.load_module
        }
        self._coroutines = []
        self._loop = asyncio.get_event_loop()
        self._initializing_mode = True

    @property
    def template_file_path(self):
        """
        Get path to template file

        :return: str -- path to template file
        """
        return self._template_file

    @property
    def output_file_path(self):
        """
        Get output path

        :return: str -- output path
        """
        return self._output_file

    def load_module(self, name, *args, **kwargs):
        """
        Load module
        Example: {{ load_module('loadable_module', *args, *kwargs) }}
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
        if not self._initializing_mode:
            return ''

        LOGGER.info('Loading module {} with arguments {} and {}'.format(name, args, kwargs))

        module_name, function_name = name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        module_function = getattr(module, function_name)
        future = asyncio.ensure_future(module_function(self, *args, **kwargs))

        self._coroutines.append(future)
        return ''

    def render(self, **items):
        """
        Render template and notify targets (execute bash command or send signal)

        :param items: values to update context
        :type items: dict[str, Any]
        :return: None
        """
        LOGGER.debug('Updating context')
        self._context.update(items)

        # Interrupt rendering if we are in initializing mode
        if self._initializing_mode:
            return None

        LOGGER.debug('Rendering')
        # Render and update target file
        content = self._template.render(self._context)
        with open(self._output_file, 'w') as file_stream:
            file_stream.write(content)

        # Notify targets
        if self._command:
            os.system(self._command)
        if self._signal and self._pid:
            os.kill(self._pid, self._signal)
        if self._signal and self._pid_file and os.path.exists(self._pid_file):
            with open(self._pid_file) as pf:
                pid = pf.read().strip()
                if not pid.isdigit():
                    raise ValueError('PID "{}" is not an integer'.format(pid))
                os.kill(int(pid), self._signal)

    def render_loop(self):
        """
        Start render loop

        :return: None
        """
        # Load modules by rendering template
        LOGGER.debug('Staring module initialization')
        self._initializing_mode = True
        self._template.render(self._context)
        self._initializing_mode = False
        LOGGER.debug('Modules have been initialized')

        # Do first render
        LOGGER.debug('Staring first render')
        self.render()

        # Check is any courutine present
        if not self._coroutines:
            raise Exception('Template doesnt use any plugin')

        # Start loop
        LOGGER.debug('Staring loop')
        result = self._loop.run_until_complete(asyncio.wait(self._coroutines))
        LOGGER.debug('Loop finished')

        if result is not None and type(result) == tuple and len(result) > 0 and type(result[0]) == set:
            task = result[0].pop()
            if type(task) == Task and task.exception() is not None:
                raise task.exception()


class SilentUndefined(Undefined):
    """
    SilentUndefined class is a replacement for original Undefined class in Jinja2,
    which is used to raise an Error if undefined variable is met in template.
    Now it doesn't raise an error, just writes empty string.
    """

    def _fail_with_undefined_error(self, *args, **kwargs):
        """
        Return an empty string instead of raise an Error.
        It's a replacement for an original _fail_with_undefined_error
        function, which is used to raise an Error.
        """
        class EmptyString(str):
            """
            A simple empty string wrapper.
            """

            def __call__(self, *args, **kwargs):
                """
                Overload call method

                :param args: args
                :param kwargs: kwargs
                :return: str -- empty string
                """
                return ''

        return EmptyString()

    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
        __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = __int__ = \
        __float__ = __complex__ = __pow__ = __rpow__ = \
        _fail_with_undefined_error
