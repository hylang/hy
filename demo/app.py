from hy.compiler.ast27 import forge_ast
from hy.lex.tokenize import tokenize
import codegen
import sys

from flask import Flask, render_template, request
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/popup')
def popup():
    return render_template('popover.html')


@app.route('/translate', methods=['POST'])
def translate():
    lines = request.form['code']

    try:
        code = tokenize(lines)
        ast = forge_ast("stdin", code)
        return codegen.to_source(ast)
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(debug=True)
