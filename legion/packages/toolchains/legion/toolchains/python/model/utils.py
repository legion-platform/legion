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
from PIL import Image as PYTHON_Image


def load_image(path):
    """
    Load image for model

    :param path: path to local image
    :type path: str
    :return: bytes -- image content
    """
    with PYTHON_Image.open(path) as image:
        if not isinstance(image, PYTHON_Image.Image):
            raise Exception('Invalid image type')

        with open(path, 'rb') as stream:
            return stream.read()
