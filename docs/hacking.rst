===============
 Hacking on hy
===============

.. highlight:: bash

Join our hyve!
==============

Please come hack on hy!

Please come hang out with us on ``#hy`` on ``irc.freenode.net``!

Please talk about it on Twitter with the ``#hy`` hashtag!

Please blog about it!

Please don't spraypaint it on your neighbor's fence (without asking nicely)!


Hack!
=====

Do this:

1. create a `virtual environment
   <https://pypi.python.org/pypi/virtualenv>`_::

       $ virtualenv venv

   and activate it::

       $ . venv/bin/activate

   or use `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/#introduction>`_
   to create and manage your virtual environment::

       $ mkvirtualenv hy
       $ workon hy

2. get the source code::

       $ git clone https://github.com/hylang/hy.git

   or use your fork::

       $ git clone git@github.com:<YOUR_USERNAME>/hy.git
3. install for hacking::

       $ cd hy/
       $ pip install -e .

4. install other develop-y requirements::

       $ pip install -r requirements-dev.txt

5. do awesome things; make someone shriek in delight/disgust at what
   you have wrought.


Test!
=====

Tests are located in ``tests/``. We use `nose
<https://nose.readthedocs.org/en/latest/>`_.

To run the tests::

    $ nosetests

Write tests---tests are good!

Also, it is good to run the tests for all the platforms supported and for pep8 compliant code. 
You can do so by running tox::

    $ tox

Document!
=========

Documentation is located in ``docs/``. We use `Sphinx
<http://sphinx-doc.org/>`_.

To build the docs in HTML::

    $ cd docs
    $ make html

Write docs---docs are good! Even this doc!


Contributing
============

.. include:: ../CONTRIBUTING.rst

Core Team
=========

Core development team of hy consists of following developers.

.. include:: coreteam.rst
