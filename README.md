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

Specifically, we propose adding these tests to CPython's CI suite,
and [gave a talk](https://us.pycon.org/2020/events/languagesummit/) at the
[2020 Language Summit](https://pyfound.blogspot.com/2020/05/property-based-testing-for-python.html)
to that effect.  Doing so would mean:

- New code can be developed with property-based tests - some already is, but
  [adding it to CPython CI would catch bugs](https://twitter.com/pganssle/status/1193371087968591872).
- Tests for existing code can be _augumented_ with property-based tests where
  this seems particularly valuable - e.g. `tests/test_source_code.py` in this repo
  has discovered several bugs.
- Property-based testing can be adopted incrementally.  _Replacing_ existing
  tests is an explicit non-goal of this project.

[PyPy already uses Hypothesis](https://github.com/Zac-HD/stdlib-property-tests/issues/7),
and sharing as much of the test suite as possible between implementations would be great.
How this would work depends largely on CPython's decisions, though.


## LICENSE
By contributing to this repository, you agree to license the contributed
code under user's choice of the Mozilla Public License Version 2.0, and
the Apache License 2.0.

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
- [Carl Friedrich Bolz-Tereick](http://cfbolz.de/)


## Trophy Case
Bugs found via this specific project:

- [BPO-40661, a segfault in the new parser](https://bugs.python.org/issue40661),
  was given maximum priority and blocked the planned release of CPython 3.9 beta1.
- [BPO-38953](https://bugs.python.org/issue38953) `tokenize.tokenize` ->
  `tokenize.untokenize` does not round-trip as documented.
  Nor, for that matter, do the `tokenize`/`untokenize` functions in
  `lib2to3.pgen.tokenize`.
- [PEP-615 (zoneinfo)](https://github.com/pganssle/zoneinfo/pull/32/commits/dc389beaaeaa702361fd186d8581da20dda807bb)
  `fold` detection failed for early transitions when the number of elapsed
  seconds is too large to fit in a C integer; and
  [a `fold` inconsistency](https://github.com/pganssle/zoneinfo/pull/41)
  where first offset handling was broken in the C extension.


## Further reading

- Hypothesis' [website](https://hypothesis.works/),
  [documentation](https://hypothesis.readthedocs.io/),
  [GitHub repo](https://github.com/HypothesisWorks/hypothesis)
- [Introductory articles](https://hypothesis.works/articles/intro/),
  [simple properties](https://fsharpforfunandprofit.com/posts/property-based-testing-2/),
  [metamorphic properties](https://www.hillelwayne.com/post/metamorphic-testing/)
- Related thoughts from
  [hardware testing and verification](https://danluu.com/testing/),
  [testing a screencast editor](https://wickstrom.tech/programming/2019/03/02/property-based-testing-in-a-screencast-editor-introduction.html),
  [PBT in Erlang / Elixr](https://propertesting.com/toc.html),
  [testing C code using Hypothesis](https://engineering.backtrace.io/posts/2020-03-11-how-hard-is-it-to-guide-test-case-generators-with-branch-coverage-feedback/)
- [`python-afl`](https://github.com/jwilk/python-afl) or
  [OSS-FUZZ](https://github.com/google/oss-fuzz) could work very nicely with
  [Hypothesis' fuzz support](https://hypothesis.readthedocs.io/en/latest/details.html#use-with-external-fuzzers)
- [`hypothesmith`](https://github.com/Zac-HD/hypothesmith)
  generates syntatically-valid but weird Python source code
  (e.g. [BPO-38953](https://bugs.python.org/issue38953) or
  [psf/black#970](https://github.com/psf/black/issues/970)).
  [Using a syntax tree](https://github.com/Zac-HD/hypothesmith/issues/2)
  for semantic validity is the logical next step.
