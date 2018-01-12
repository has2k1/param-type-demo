import re
import ast
import sys
import os
import pkgutil
import importlib
from functools import lru_cache
from types import ModuleType, MethodType, FunctionType

from plotnine.doctools import docstring_section_lines
from numpydoc.xref import make_xref_param_type
from tabulate import tabulate


DOCSTRING_SECTIONS = {
    'parameters', 'see also', 'note', 'notes',
    'yields', 'returns',
    'example', 'examples'}

SPEC_RE = re.compile(r'^\w+\s:\s(.+$)')


def all_docstrings_in_body(ast_body):
    for node in ast_body:
        if isinstance(node, ast.FunctionDef):
            s = ast.get_docstring(node)
            if s:
                yield s
            else:
                continue
        elif isinstance(node, ast.ClassDef):
            yield ast.get_docstring(node)
            yield from all_docstrings_in_body(node.body)


def all_python_files(top_path):
    for root, dirs, files in os.walk(top_path):
        for file in files:
            if file.endswith('.py'):
                yield f'{root}/{file}'


def all_docstrings_in_path(top_path):
    for filename in all_python_files(top_path):
        with open(filename) as f:
            try:
                contents = f.read()
            except Exception as e:
                print(f'Read Error - {e.__class__.__name__}: {filename}',
                      file=sys.stderr)
                continue

            try:
                module = ast.parse(contents)
            except Exception as e:
                print(f'Parse Error - {e.__class__.__name__}: {filename}',
                      file=sys.stderr)
                continue
        yield from all_docstrings_in_body(module.body)


def all_parameter_sections(top_path):
    for doc in all_docstrings_in_path(top_path):
        if not doc:
            continue
        section = docstring_section_lines(doc, 'parameters')
        if section:
            yield section


def all_parameter_section_specs(top_path):
    for section in all_parameter_sections(top_path):
        for line in section.split('\n'):
            m = SPEC_RE.match(line)
            if m:
                yield m.group(1)


def main():
    libs = {
        'numpy': '/home/hassan/scm/python/numpy/numpy',
        'scipy': '/home/hassan/scm/python/scipy/scipy',
        'matplotlib': '/home/hassan/scm/python/matplotlib/lib',
        'pandas': '/home/hassan/scm/python/pandas/pandas',
        'sklearn': '/home/hassan/scm/python/scikit-learn/sklearn',
        'plotnine': '/home/hassan/scm/python/plotnine/plotnine',
        'plydata': '/home/hassan/scm/python/plydata/plydata',
        'mizani': '/home/hassan/scm/python/mizani/mizani',
        'statsmodels': '/home/hassan/scm/python/statsmodels/statsmodels',
    }

    xref_aliases = {
        # python
        'sequence': ':term:`python:sequence`',
        'iterable': ':term:`python:iterable`',
        'class': ':term:`python:class`',
        'lambda': ':term:`python:lambda`',
        'file-like': ':term:`file-like<python:file-like object>`',
        'file_like': ':term:`file_like<python:file-like object>`',
        'string': 'str',
        'strings': 'str',
        'dictionary': 'dict',
        'dictionaries': 'dict',
        'tuples': 'tuple',
        'boolean': 'bool',
        'integer': 'int',
        'integers': 'int',
        'Integer': 'int',
        'ints': 'int',
        'floats': 'float',
        'double': 'float',
        # numpy
        'array': 'numpy.ndarray',
        'dtype': 'numpy.dtype',
        'ndarray': 'numpy.ndarray',
        'matrix': 'numpy.matrix',
        'MaskedArray': 'numpy.ma.MaskedArray',
        'array-like': ':term:`array-like<numpy:array_like>`',
        'array_like': ':term:`numpy:array_like`',
        # scipy
        'sparse': 'scipy.sparse.spmatrix',
        # pandas
        'dataframe': 'pandas.DataFrame',
        'DataFrame': 'pandas.DataFrame',
        'Series': 'pandas.Series',
        'series': 'pandas.Series',
    }

    xref_ignore = {'default', 'optional'}

    def generate_rows(param_types):
        for param_type in sorted(set(param_types)):
            xref = make_xref_param_type(
                param_type, xref_aliases, xref_ignore)
            row = (f'- {param_type}\n- {xref}',)
            yield row

    for name, path in libs.items():
        param_type_it = all_parameter_section_specs(path)
        table_str = tabulate(
            generate_rows(param_type_it),
            tablefmt='grid')

        with open(f'source/{name}-param-types.rst', 'w') as f:
            f.writelines([f'{name}\n', '-'*len(name) + '\n'])
            f.write(table_str)


if __name__ == '__main__':
    main()
