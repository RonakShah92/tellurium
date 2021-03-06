# coding: utf-8
"""
Utilities to work with ipython notebooks.
"""
from __future__ import print_function, division

import io
import os
import sys
import types
import IPython
from IPython.core.interactiveshell import InteractiveShell


def find_notebook(fullname, path=None):
    """ Find a notebook, given its fully qualified name and an optional path.
    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.

    :param fullname: name of notebook (without .ipynb extension)
    :type fullname: str
    :param path: relative path information for search
    :type path: str
    :return: path of notebook
    :rtype: str
    """

    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            return nb_path


class NotebookLoader(object):
    """ Module Loader for IPython Notebooks. """
    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """ Import a notebook as a module. """
        path = find_notebook(fullname, self.path)

        print ("importing IPython notebook from %s" % path)

        # load the notebook object
        with io.open(path, 'r', encoding='utf-8') as f:
            nb = IPython.nbformat.read(f, IPython.nbformat.NO_CONVERT)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            for cell in nb.worksheets[0].cells:
                if cell.cell_type == 'code' and cell.language == 'python':
                    # transform the input to executable Python
                    code = self.shell.input_transformer_manager.transform_cell(
                        cell.input
                    )
                    # run the code in themodule
                    exec(code, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns
        return mod


class NotebookFinder(object):
    """Module finder that locates IPython Notebooks"""
    def __init__(self):
        self.loaders = {}

    def find_module(self, fullname, path=None):
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]


def loadNotebooksAsModules():
    sys.meta_path.append(NotebookFinder())


def sideBySideOutput():
	print('''
For side-by-side output, add this to a new cell:

%%html
<style>
div.cell {box-orient:horizontal;flex-direction:row;}
div.cell *{width:100%;}div.prompt{width:80px;}</style>
''')

