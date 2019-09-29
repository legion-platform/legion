import re

from legion.packager.rest.data_models import DEFAULT_IMAGE_NAME_TEMPLATE
from legion.packager.rest.utils import build_image_name, TemplateNameValues


def test_without_template() -> None:
    """
    build_image_name should work if we don't pass a Jinja template
    """
    docker_image_name = "test:1234"

    result = build_image_name(docker_image_name, TemplateNameValues(Name='name', Version='version'))
    assert docker_image_name == result


def test_basic_template_name() -> None:
    result = build_image_name('{{ Name }}/{{ RandomUUID }}:{{ Version }}',
                              TemplateNameValues(Name='name', Version='version', RandomUUID="1234"))
    assert 'name/1234:version' == result


def test_empty_random_uuid() -> None:
    result = build_image_name('{{ Name }}/{{ RandomUUID }}:{{ Version }}',
                              TemplateNameValues(Name='name', Version='version'))

    assert re.match(r'name/([\d\w\-]+):version', result)


def test_default_image_template_name() -> None:
    """
    Check that the default image template works as expected
    """
    result = build_image_name(DEFAULT_IMAGE_NAME_TEMPLATE,
                              TemplateNameValues(Name='name', Version='version'))

    assert re.match(r'name-version:([\d\w\-]+)', result)
