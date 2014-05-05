Contributions are welcome & greatly appreciated, every little bit
helps in making Hy more awesome.

Pull requests are great! We love them, here is a quick guide:

- Fork the repo, create a topic branch for a feature/fix. Avoid
  making changes directly on the master branch

- All incoming features should be accompanied with tests

- Before you submit a PR, please run the tests and check your code
  against the style guide.  You can do both these things at once::

    $ make d

- Make commits into logical units, so that it is easier to track &
  navigate later. Before submitting a PR, try squashing the commits
  into changesets that are easy to come back to later. Also make sure
  you don't leave spurious whitespace in the changesets, this avoids
  creation of whitespace fix commits later.

- As far as commit messages go, try to adhere to
  the following:

  + Try sticking to the 50 character limit for the first line of git
    commit messages

  + For more explanations etc. follow this up with a blank line and
    continue describing the commit in detail


- Finally add yourself to the AUTHORS file (as a separate commit), you
  deserve it :)

- All incoming changes need to be acked by 2 different members of
  Hylang's core team. Additional review is clearly welcome, but we need
  a minimum of 2 signoffs for any change.

- If a core member is sending in a PR, please find 2 core members that doesn't
  include the PR submitter. The idea here is that one can work with the PR
  author, and a second acks the entire change set.

- For documentation & other trivial changes, we're good to merge after one
  ACK. We've got low coverage, so it'd be great to keep that barrier low.
