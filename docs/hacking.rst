===============
 Hacking on Hy
===============

.. highlight:: bash

Join our Hyve!
==============

Please come hack on Hy!

Please come hang out with us on ``#hy`` on ``irc.freenode.net``!

Please talk about it on Twitter with the ``#hy`` hashtag!

Please blog about it!

Please don't spraypaint it on your neighbor's fence (without asking nicely)!


Hack!
=====

Do this:

1. Create a `virtual environment
   <https://pypi.python.org/pypi/virtualenv>`_::

       $ virtualenv venv

   and activate it::

       $ . venv/bin/activate

   or use `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/#introduction>`_
   to create and manage your virtual environment::

       $ mkvirtualenv hy
       $ workon hy

2. Get the source code::

       $ git clone https://github.com/hylang/hy.git

   or use your fork::

       $ git clone git@github.com:<YOUR_USERNAME>/hy.git

3. Install for hacking::

       $ cd hy/
       $ pip install -e .

4. Install other develop-y requirements::

       $ pip install -r requirements-dev.txt

5. Do awesome things; make someone shriek in delight/disgust at what
   you have wrought.


Test!
=====

Tests are located in ``tests/``. We use `nose
<https://nose.readthedocs.org/en/latest/>`_.

To run the tests::

    $ nosetests

Write tests---tests are good!

Also, it is good to run the tests for all the platforms supported and for
PEP 8 compliant code. You can do so by running tox::

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

The core development team of Hy consists of following developers:

.. include:: coreteam.rst
