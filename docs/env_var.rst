=====================
Environment variables
=====================

Hy treats the following environment variables specially. Boolean environment
variables are interpreted as false when set to the empty string and true when
set to anything else.

.. envvar:: HYSTARTUP

   (Default: nothing) Path to a file containing Hy source code to execute when
   starting the REPL.

.. envvar:: HY_SHOW_INTERNAL_ERRORS

   (Default: false) Whether to show some parts of tracebacks that point to
   internal Hy code and won't be helpful to the typical Hy user.

.. envvar:: HY_HISTORY

   (Default: ``~/.hy-history``) Path to which REPL input history will be saved.

.. envvar:: HY_MESSAGE_WHEN_COMPILING

   (Default: false) Whether to print "Compiling FILENAME" to standard error
   before compiling each file of Hy source code. This is helpful for debugging
   whether files are being loaded from bytecode or re-compiled.
