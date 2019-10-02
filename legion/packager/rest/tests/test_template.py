from legion.packager.rest.constants import DESCRIPTION_TEMPLATE
from legion.packager.rest.template import render_packager_template


def test_render_packager_template():
    values = dict(
        model_name="test",
        model_version='7.8.9',
        legion_version='4.5.6',
        packager_version='1.2.3',
    )

    rendered_description = render_packager_template(DESCRIPTION_TEMPLATE, values)
    for _, value in values.items():
        assert value in rendered_description
