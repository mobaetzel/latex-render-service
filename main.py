from hashlib import sha1
from json import dumps
from os import path, makedirs
from pathlib import Path as PathlibPath
from subprocess import run
from typing import Dict, Union

from flask import Flask, request, abort, send_file
from flask_cors import CORS
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from yaml import safe_load

# Determine the current directory.
__DIR__ = PathlibPath(__file__).parent.resolve()

# Parse the config file for later use.
with open(path.join(__DIR__, 'conf', 'conf.yml'), 'r') as stream:
    __CONF__ = safe_load(stream)
__SV__ = __CONF__.get('server', {})

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

# Start the flask app and set the CORS settings.
app = Flask(__name__)
CORS(app, origins=__SV__.get('origins', []))


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


@app.route('/render/<string:template_id>', methods=['POST'])
def render(template_id: str):
    """
    Handle the template rendering.
    :param template_id: The Id of the template to render.
    :return: The filename of the rendered template.
    """

    # Check the authorization.
    auth = request.headers.get('authorization')
    if auth not in __CONF__.get('secrets', []):
        abort(401)

    # Check the payload.
    request_payload = request.get_json()
    if request_payload is None:
        abort(400)

    # Render the template and receive the rendered file path.
    file_hash = render_template(template_id, request_payload)
    if file_hash is None:
        abort(404)

    # Respond the access url of the rendered template.
    return '{}/cache/{}'.format(__SV__.get('host'), file_hash)


def render_template(template_id: str, context: Dict) -> Union[str, None]:
    """
    Render a template based on the template id and the context.
    :param template_id: The id of the template to load.
    :param context: The context dict which is used for rendering.
    :return: The filename of the rendered template or None if no template with the given id was found.
    """

    # Stringify the context and create a hash for caching.
    context_str = template_id + dumps(context, sort_keys=True, default=str)
    sha1_hasher = sha1(context_str.encode('utf-8'))
    context_hash = sha1_hasher.hexdigest()
    output_filename = context_hash + '.pdf'

    # Determine the path of the output file to check or render to.
    # This utilizes the hash for caching.
    output_path = path.join(__DIR__, 'cache', output_filename)

    # Check if the file already exists and return it accordingly.
    if path.isfile(output_path):
        return output_filename

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

    # Return the filename of the rendered pdf file.
    return output_filename


@app.route('/cache/<string:filename>', methods=['GET'])
def cache(filename: str):
    """
    Return a cached file based on the filename or 404 if not found.
    :param filename: The name of the file.
    :return: The cached file.
    """
    file_path = path.join(__DIR__, 'cache', filename)
    if not path.isfile(file_path):
        abort(404)

    custom_filename = request.args.get('filename', filename, type=str)
    return send_file(file_path, attachment_filename=custom_filename)
