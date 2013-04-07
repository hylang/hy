===============
 Hacking on hy
===============

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

1. create a `Python virtual environment
   <https://pypi.python.org/pypi/virtualenv>`_
2. (optional) go to https://github.com/paultag/hy and fork it
3. get the source code::

       $ git clone git://github.com/paultag/hy.git

   (or use your fork)
4. install for hacking::

       $ python setup.py develop

5. install other develop-y requirements::

       $ pip install -r requirements-dev.txt

6. do awesome things; make someone shriek in delight/disgust at what
   you have wrought


Test!
=====

Tests are located in ``tests/``. We use `nose
<https://nose.readthedocs.org/en/latest/>`_.

To run the tests::

    $ nosetests

Write tests---tests are good!


Document!
=========

Documentation is located in ``docs/``. We use `Sphinx
<http://sphinx-doc.org/>`_.

To build the docs in html::

    $ cd docs
    $ make html

Write docs---docs are good! Even this doc!
