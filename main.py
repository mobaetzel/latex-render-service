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

__DIR__ = pathlib.Path(__file__).parent.resolve()

with open(path.join(__DIR__, 'conf', 'conf.yml'), 'r') as stream:
    __CONF__ = safe_load(stream)

latex_jinja_env = Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=FileSystemLoader(path.join(__DIR__, 'templates'))
)

app = Flask(__name__)
CORS(app, origins=__CONF__['server']['origins'])


def prepare_dirs():
    def mkdir(dir_path):
        if not path.exists(dir_path):
            makedirs(dir_path)
    mkdir(path.join(__DIR__, 'cache'))


prepare_dirs()


def load_template(template_id: str, context: Dict) -> Union[str, None]:
    context_str = template_id + dumps(context, sort_keys=True, default=str)
    hash_object = sha1(context_str.encode('utf-8'))
    hash_hex = hash_object.hexdigest()

    output_path = path.join(__DIR__, 'cache', hash_hex + '.pdf')

    if path.isfile(output_path):
        return output_path

    input_template_file = template_id + '.tex'

    try:
        input_template = latex_jinja_env.get_template(input_template_file)
    except TemplateNotFound:
        return None
    rendered_input_template = input_template.render(**context)

    run(
        ['pandoc', '--from=latex', '--to=pdf', '-o', output_path],
        input=rendered_input_template,
        encoding='utf-8',
    )

    return output_path


@app.route('/<string:template_id>', methods=['POST'])
def render(template_id: str):
    auth = request.headers.get('authorization')
    if auth not in __CONF__['secrets']:
        abort(401)

    request_payload = request.get_json()
    if request_payload is None:
        abort(400)

    output_path = load_template(template_id, request_payload)
    if output_path is None:
        abort(404)

    return send_file(output_path, attachment_filename=template_id + '.pdf')
