Contributor Guidelines
======================

Contributions are welcome and greatly appreciated. Every little bit
helps in making Hy better. Potential contributions include:

- Reporting and fixing bugs.
- Requesting features.
- Adding features.
- Writing tests for outstanding bugs or untested features.
  - You can mark tests that Hy can't pass yet as xfail_.
- Cleaning up the code.
- Improving the documentation.
- Answering questions on `the IRC channel`_, `the mailing list`_, or
  `Stack Overflow`_.
- Evangelizing for Hy in your organization, user group, conference, or
  bus stop.

Issues
~~~~~~

In order to report bugs or request features, search the `issue tracker`_ to
check for a duplicate. (If you're reporting a bug, make sure you can
reproduce it with the very latest, bleeding-edge version of Hy from
the ``master`` branch on GitHub. Bugs in stable versions of Hy are
fixed on ``master`` before the fix makes it into a new stable
release.) If there aren't any duplicates, then you can make a new issue.

It's totally acceptable to create an issue when you're unsure whether
something is a bug or not. We'll help you figure it out.

Use the same issue tracker to report problems with the documentation.

Pull requests
~~~~~~~~~~~~~

Submit proposed changes to the code or documentation as pull requests
(PRs) on GitHub_. Git can be intimidating and confusing to the
uninitiated. `This getting-started guide`_ may be helpful. However, if
you're overwhelmed by Git, GitHub, or the rules below, don't sweat
it. We want to keep the barrier to contribution low, so we're happy to
help you with these finicky things or do them for you if necessary.

Deciding what to do
-------------------

Issues tagged good-first-bug_ are expected to be relatively easy to
fix, so they may be good targets for your first PR for Hy.

If you're proposing a major change to the Hy language, or you're
unsure of the proposed change, create an issue to discuss it before
you write any code. This will allow others to give feedback on your
idea, and it can avoid wasted work.

File headers
------------

Every Python or Hy file in the source tree that is potentially
copyrightable should have the following header (but with ``;;`` in
place of ``#`` for Hy files)::

      # Copyright [current year] the authors.
      # This file is part of Hy, which is free software licensed under the Expat
      # license. See the LICENSE.

As a rule of thumb, a file can be considered potentially copyrightable
if it includes at least 10 lines that contain something other than
comments or whitespace. If in doubt, include the header.

Commit formatting
-----------------

Many PRs are small enough that only one commit is necessary, but
bigger ones should be organized into logical units as separate
commits. PRs should be free of merge commits and commits that fix or
revert other commits in the same PR (``git rebase`` is your friend).

Avoid committing spurious whitespace changes.

The first line of a commit message should describe the overall change in 50
characters or less. If you wish to add more information, separate it from the
first line with a blank line.

Testing
-------

New features and bug fixes should be tested. If you've caused an
xfail_ test to start passing, remove the xfail mark. If you're
testing a bug that has a GitHub issue, include a comment with the URL
of the issue.

No PR may be merged if it causes any tests to fail. You can run the
test suite and check the style of your code with ``make d``. The byte-compiled
versions of the test files can be purged using ``git clean -dfx tests/``.
If you want to run the tests while skipping the slow ones in ``test_bin.py``,
use ``pytest --ignore=tests/test_bin.py``.

NEWS and AUTHORS
----------------

If you're making user-visible changes to the code, add one or more
items describing it to the NEWS file.

Finally, add yourself to the AUTHORS file (as a separate commit): you
deserve it. :)

The PR itself
-------------

PRs should ask to merge a new branch that you created for the PR into
hylang/hy's ``master`` branch, and they should have as their origin
the most recent commit possible.

If the PR fulfills one or more issues, then the body text of the PR
(or the commit message for any of its commits) should say "Fixes
#123" or "Closes #123" for each affected issue number. Use this exact
(case-insensitive) wording, because when a PR containing such text is
merged, GitHub automatically closes the mentioned issues, which is
handy. Conversely, avoid this exact language if you want to mention
an issue without closing it (because e.g. you've partly but not
entirely fixed a bug).

There are two situations in which a PR is allowed to be merged:

1. When it is approved by **two** members of Hy's core team other than the PR's
   author. Changes to the documentation, or trivial changes to code, need only
   **one** approving member.
2. When the PR is at least **two weeks** old and **no** member of the Hy core
   team has expressed disapproval of the PR in its current state. (Exception: a
   PR to create a new release is not eligible to be merged under this criterion,
   only the first one.)

Anybody on the Hy core team may perform the merge. Merging should create a
merge commit (don't squash unnecessarily, because that would remove separation
between logically separate commits, and don't fast-forward, because that would
throw away the history of the commits as a separate branch), which should
include the PR number in the commit message.

Contributor Code of Conduct
===========================

As contributors and maintainers of this project, we pledge to respect
all people who contribute through reporting issues, posting feature
requests, updating documentation, submitting pull requests or patches,
and other activities.

We are committed to making participation in this project a
harassment-free experience for everyone, regardless of level of
experience, gender, gender identity and expression, sexual
orientation, disability, personal appearance, body size, race,
ethnicity, age, or religion.

Examples of unacceptable behavior by participants include the use of
sexual language or imagery, derogatory comments or personal attacks,
trolling, public or private harassment, insults, or other
unprofessional conduct.

Project maintainers have the right and responsibility to remove, edit,
or reject comments, commits, code, wiki edits, issues, and other
contributions that are not aligned to this Code of Conduct. Project
maintainers who do not follow the Code of Conduct may be removed from
the project team.

This code of conduct applies both within project spaces and in public
spaces when an individual is representing the project or its
community.

Instances of abusive, harassing, or otherwise unacceptable behavior
may be reported by opening an issue or contacting one or more of the
project maintainers.

This Code of Conduct is adapted from the `Contributor Covenant`_,
version 1.1.0, available at
http://contributor-covenant.org/version/1/1/0/.

.. _Contributor Covenant: http://contributor-covenant.org
.. _issue tracker: https://github.com/hylang/hy/issues
.. _GitHub: https://github.com/hylang/hy
.. _This getting-started guide: http://rogerdudler.github.io/git-guide/
.. _good-first-bug: https://github.com/hylang/hy/issues?q=is%3Aissue+is%3Aopen+label%3Agood-first-bug
.. _the IRC channel: irc://freenode.net/hy
.. _the mailing list: https://groups.google.com/forum/#!forum/hylang-discuss
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/hy
.. _xfail: https://docs.pytest.org/en/latest/skipping.html#mark-a-test-function-as-expected-to-fail
