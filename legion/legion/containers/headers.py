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
legion headers (for meta-information)
"""

STDERR_PREFIX = 'X-Legion-'

MODEL_ID = 'Model-Id'
MODEL_PATH = 'Model-Path'
MODEL_VERSION = 'Model-Version'
IMAGE_TAG_EXTERNAL = 'Model-Image-Tag-External'
IMAGE_TAG_LOCAL = 'Model-Image-Tag-Local'
SAVE_STATUS = 'Save-Status'

DOMAIN_PREFIX = 'com.epam.'
DOMAIN_MODEL_ID = DOMAIN_PREFIX + 'legion.model.id'
DOMAIN_MODEL_VERSION = DOMAIN_PREFIX + 'legion.model.version'
DOMAIN_CLASS = DOMAIN_PREFIX + 'legion.class'
DOMAIN_CONTAINER_TYPE = DOMAIN_PREFIX + 'legion.container_type'
DOMAIN_CONTAINER_DESCRIPTION = DOMAIN_PREFIX + 'legion.container_description'
DOMAIN_MODEL_PROPERTY_VALUES = DOMAIN_PREFIX + 'legion.model.property_values'
DOMAIN_MODEL_PROPERTY_TYPE = DOMAIN_PREFIX + 'legion.property'
