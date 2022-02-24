from flask import Flask, send_file, request, abort
from subprocess import run
from os import path, makedirs
import pathlib
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from json import dumps
from hashlib import sha1
from typing import Dict, Union
from yaml import safe_load
from flask_cors import CORS

# Determine the current directory.
__DIR__ = pathlib.Path(__file__).parent.resolve()

# Parse the config file for later use.
with open(path.join(__DIR__, 'conf', 'conf.yml'), 'r') as stream:
    __CONF__ = safe_load(stream)

# Prepare jinja environment with special control sequences for the latex environment.
latex_jinja_env = Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',
    variable_start_string=r'\VAR{',
    variable_end_string='}',
    comment_start_string=r'\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=FileSystemLoader(path.join(__DIR__, 'templates'))
)

# Start the flas app and set the CORS settings.
app = Flask(__name__)
CORS(app, origins=__CONF__['server']['origins'])


def prepare_dirs() -> None:
    """
    Prepare all required directories.
    """

    def mkdir(dir_path) -> None:
        """
        Create a directory if it not yet exits.
        """
        if not path.exists(dir_path):
            makedirs(dir_path)

    mkdir(path.join(__DIR__, 'cache'))


# Execute the directory preparation.
prepare_dirs()


def render_template(template_id: str, context: Dict) -> Union[str, None]:
    """
    Render a template based on the template id and the context.
    :param template_id: The id of the template to load.
    :param context: The context dict which is used for rendering.
    :return: The filepath of the rendered template or None if no template with the given id was found.
    """

    # Stringify the context and create a hash for caching.
    context_str = template_id + dumps(context, sort_keys=True, default=str)
    hash_object = sha1(context_str.encode('utf-8'))
    hash_hex = hash_object.hexdigest()

    # Determine the path of the output file to check or render to.
    # This utilizes the hash for caching.
    output_path = path.join(__DIR__, 'cache', hash_hex + '.pdf')

    # Check if the file already exists and return it accordingly.
    if path.isfile(output_path):
        return output_path

    # Determine the name of the input file based in the template id.
    input_template_file = template_id + '.tex'

    # Try to render the template with the given context.
    try:
        input_template = latex_jinja_env.get_template(input_template_file)
    except TemplateNotFound:
        return None
    rendered_input_template = input_template.render(**context)

    # Run the pandoc shell command and use the rendered template as a stdin value.
    # The pdf file is rendered to the output path.
    run(
        ['pandoc', '--from=latex', '--to=pdf', '-o', output_path],
        input=rendered_input_template,
        encoding='utf-8',
    )

    # Return the path of the rendered pdf file.
    return output_path


@app.route('/<string:template_id>', methods=['POST'])
def render(template_id: str):
    """
    Handle the template rendering.
    :param template_id: The Id of the template to render.
    :return: A flask response object.
    """

    # Check the authorization.
    auth = request.headers.get('authorization')
    if auth not in __CONF__['secrets']:
        abort(401)

    # Check the payload.
    request_payload = request.get_json()
    if request_payload is None:
        abort(400)

    # Render the template and receive the rendered file path.
    output_path = render_template(template_id, request_payload)
    if output_path is None:
        abort(404)

    # Respond the rendered file based on the filepath.
    return send_file(output_path, attachment_filename=template_id + '.pdf')
