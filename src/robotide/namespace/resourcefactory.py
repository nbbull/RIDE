#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
from robot.parsing.model import ResourceFile

from robotide import utils


class ResourceFactory(object):
    _IGNORE_RESOURCE_DIRECTORY_SETTING_NAME = 'ignored resource directory'

    def __init__(self, settings):
        self.cache = {}
        self.python_path_cache = {}
        exclude_directory = settings.get(self._IGNORE_RESOURCE_DIRECTORY_SETTING_NAME, None)
        self._exclude_directory = exclude_directory and self._with_separator(self._normalize(exclude_directory))
        self._set_pythonpath(settings.get('pythonpath', []))
        settings.add_change_listener(self)

    def _with_separator(self, dir):
        return os.path.abspath(dir)+os.path.sep

    def _set_pythonpath(self, values):
        for path in values:
            if path not in sys.path:
                sys.path.insert(0, path.replace('/', os.sep))

    def setting_changed(self, name, old_value, new_value):
        if name == 'pythonpath':
            self._set_pythonpath(new_value)

    def get_resource(self, directory, name):
        path = self._build_path(directory, name)
        res = self._get_resource(path)
        if res:
            return res
        path_from_pythonpath = self._get_python_path(name)
        if path_from_pythonpath:
            return self._get_resource(path_from_pythonpath)
        return None

    def _build_path(self, directory, name):
        path = os.path.join(directory, name) if directory else name
        return os.path.abspath(path)

    def get_resource_from_import(self, import_, retriever_context):
        resolved_name = retriever_context.vars.replace_variables(import_.name)
        return self.get_resource(import_.directory, resolved_name)

    def new_resource(self, directory, name):
        path = os.path.join(directory, name) if directory else name
        path = self._normalize(path)
        resource = ResourceFile(source=path)
        self.cache[path] = resource
        return resource

    def resource_filename_changed(self, old_name, new_name):
        self.cache[self._normalize(new_name)] = self._get_resource(old_name)
        del self.cache[self._normalize(old_name)]

    def _get_python_path(self, name):
        if name not in self.python_path_cache:
            path_from_pythonpath = utils.find_from_pythonpath(name)
            self.python_path_cache[name] = path_from_pythonpath
        return self.python_path_cache[name]

    def _get_resource(self, path):
        normalized = self._normalize(path)
        if self._exclude_directory and normalized.startswith(self._exclude_directory):
            return None
        if normalized not in self.cache:
            try:
                self.cache[normalized] = self._load_resource(path)
            except Exception:
                self.cache[normalized] = None
                return None
        return self.cache[normalized]

    def _load_resource(self, path):
        return ResourceFile(path).populate()

    def _normalize(self, path):
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))
