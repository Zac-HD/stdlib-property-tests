# stdlib-property-tests
Property-based tests for the Python standard library (and builtins)


## Goal

**Find and fix bugs in Python, *before* they ship to users.**

CPython's existing test suite is good, but bugs still slip through occasionally.
We think that using property-based testing tools - i.e.
[Hypothesis](https://hypothesis.readthedocs.io/) - can help with this.
They're no magic bullet, but computer-assisted testing techniques routinely
try inputs that humans wouldn't think of (or bother trying), and
[turn up bugs that humans missed](https://twitter.com/pganssle/status/1193371087968591872).

Writing tests that describe *every valid input* often leads to tighter
validation and cleaner designs too, even when no counterexamples are found!

We aim to have a compelling proof-of-concept by [PyCon US](https://us.pycon.org/2020/),
and be running as part of the CPython CI suite by the end of the sprints.


## LICENSE
By contributing to this repository, you agree to license the contributed
code under user's choice of the Mozilla Public License Version 2.0, and
the Python Software Foundation License Version 2.

This dual-licence is intended to make it as easy as possible for the tests
in this repository to be used upstream by the CPython project, other
implementations of Python, and the Hypothesis project and ecosystem.


# Workflow
To run the tests against the current version of Python:

- `pip install -r requirements.txt` (or `hypothesis hypothesmith`)
- `python -m unittest`

For development, we use [`tox`](https://tox.readthedocs.io/en/latest/)
to manage an extensive suite of auto-formatters and linters, so:

- `pip install tox`
- `tox`

will set up a virtualenv for you, install everything, and finally run
the formatters, linters, and test suite.


## Contributors
<!--- Add yourself to the end of the list! -->
- [Zac Hatfield-Dodds](https://zhd.dev)
- [Paul Ganssle](https://ganssle.io)
