"""
Template generator
"""

from jinja2 import Environment, PackageLoader, select_autoescape


def render_template(template_name, values=None):
    """
    Render template with parameters

    :param template_name: name of template without path (all templates should be placed in drun.templates directory)
    :param values: dict template variables or None
    :return: str rendered template
    """
    env = Environment(
        loader=PackageLoader(__name__, 'templates'),
        autoescape=select_autoescape(['tmpl'])
    )

    if not values:
        values = {}

    template = env.get_template(template_name)
    return template.render(values)
