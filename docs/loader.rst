=========
Hy Loader
=========

.. warning::
    This is incomplete; please consider contributing to the documentation
    effort.


The Loader
==========

Hy, by emits Python AST, can be directly parsed, evaluated, and executed.

Its Python interoptability is powered by PEP 302 which lets Hy hook
into the Python import logic

This lets Python (and Hy) reply directly in Python's import system and
load both Python and Hy modules.

The mechanism differs between different Python versions, and worth
highlighting the various corner cases and poops....

Python 3
--------

Implements a `meta_path` entry that provides its own `PathFinder`
which then implements its own `FileFinder` which then chains a
`Loader`.

The three parts provide a `ModuleSpec` which Python is able to then
convert into a module.

Python 2
--------

There's a simpler system here, with a `meta_path` entry provides an
`Indexer`. The indexer then finds core and returns a loader, which is
directly responsible for loading a module. When we load a module
directly.

Known Issues
------------

* The Hy metaloader must be specified first, and can't be fallen back on
* Valid Hy modules could be confused as valid Python namespace
  modules. This means that a Hy module could correctly import, but not
  contain any attributes.
* We can't support namespace modules because otherwise valid Python
  modules start looking like Hy namespace modules (reverse of the
  problem above).
