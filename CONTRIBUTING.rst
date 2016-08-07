Contributor Guidelines
======================

Contributions are welcome & greatly appreciated, every little bit
helps in making Hy more awesome.

Pull requests are great! We love them; here is a quick guide:

- `Fork the repo`_ and create a topic branch for a feature/fix. Avoid
  making changes directly on the master branch. If you would like to 
  contribute but don't know how to begin, the `good-first-bug`_ label 
  of the `issue tracker`_ is the place to go. 
  (If you're new to Git: `Start Here`_)

- All incoming features should be accompanied with tests.

- If you are contributing a major change to the Hy language (e.g. changing
  the behavior of or removing functions or macros), or you're unsure of
  the proposed change, please open an issue in the `issue tracker`_ before
  submitting the PR. This will allow others to give feedback on your idea,
  and it will avoid constant changes or wasted work. For other PRs (such as
  documentation fixes or code cleanup), you can directly open the PR without
  first opening a corresponding issue.

- Before you submit a PR, please run the tests and check your code
  against the style guide. You can do both of these things at once::

    $ make d

- Make commits into logical units, so that it is easier to track &
  navigate later. Before submitting a PR, try squashing the commits
  into changesets that are easy to come back to later. Also, make sure
  you don't leave spurious whitespace in the changesets; this avoids
  creation of whitespace fix commits later.

- As far as commit messages go, try to adhere to the following:

  + Try sticking to the 50 character limit for the first line of Git
    commit messages.

  + For more detail/explanations, follow this up with a blank line and
    continue describing the commit in detail.

- Finally, add yourself to the AUTHORS file (as a separate commit): you
  deserve it :)

- All incoming changes need to be acked by 2 different members of
  Hylang's core team. Additional review is clearly welcome, but we need
  a minimum of 2 signoffs for any change.

- If a core member is sending in a PR, please find 2 core members that doesn't
  include the PR submitter. The idea here is that one can work with the PR
  author, and a second acks the entire change set.

- For documentation & other trivial changes, we're good to merge after one
  ACK. We've got low coverage, so it'd be great to keep that barrier low.

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
.. _Fork the Repo: https://help.github.com/articles/fork-a-repo/
.. _Start Here: http://rogerdudler.github.io/git-guide/)
.. _good-first-bug: http://github.com/hylang/hy/issues?q=is%3Aissue+is%3Aopen+label%3Agood-first-bug
