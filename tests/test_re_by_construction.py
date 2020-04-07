import re
import sys
import time
import unittest

from hypothesis import given, strategies as st

IS_PYPY = hasattr(sys, "pypy_version_info")

special_characters = ".^$*+?{}\\[]-|()#=!"
MAXREPEAT = 7

counter = 0


def gensym():
    global counter
    counter += 1
    return f"symbol{counter}"


class State:
    def __init__(self):
        self.groups = {}


class CantGenerateNonMatching(Exception):
    pass


class Re:
    """ abstract base class for regular expression syntax nodes """

    def can_be_empty(self):
        """ Can self match the empty string? """
        return False

    def matching_string(self, draw, state):
        """ use draw to generate a string that is known to match self """
        raise NotImplementedError

    def non_matching_string(self, draw, state):
        """ try to use draw to generate a string that *doesn't* match self. Can
        fail by raising CantGenerateNonMatching """
        raise NotImplementedError

    def build_re(self):
        """ Build the re syntax for self """
        raise NotImplementedError


class Char(Re):
    def __init__(self, c):
        self.c = c

    def matching_string(self, draw, state):
        return self.c

    def non_matching_string(self, draw, state):
        return draw(st.characters(blacklist_characters=self.c))

    def build_re(self):
        return self.c

    @staticmethod
    def make(draw):
        exp = draw(st.characters(blacklist_characters=special_characters))
        return Char(exp)


class CharClass(Re):
    def __init__(self, char, unicat, polarity_cat):
        self.char = char
        self.unicat = unicat
        self.polarity_cat = polarity_cat

    def matching_string(self, draw, state):
        if self.polarity_cat:
            return draw(st.characters(whitelist_categories=self.unicat))
        return draw(st.characters(blacklist_categories=self.unicat))

    def non_matching_string(self, draw, state):
        if self.polarity_cat:
            return draw(st.characters(blacklist_categories=self.unicat))
        return draw(st.characters(whitelist_categories=self.unicat))

    def build_re(self):
        return "\\" + self.char

    @staticmethod
    def make(draw):
        # XXX can add more
        return CharClass(
            *draw(st.sampled_from([("d", ["Nd"], True), ("D", ["Nd"], False)]))
        )


class Dot(Re):
    def matching_string(self, draw, state):
        return draw(st.characters(blacklist_characters="\n"))

    def non_matching_string(self, draw, state):
        return "\n"

    def build_re(self):
        return "."

    @staticmethod
    def make(draw):
        return Dot()


class Escape(Re):
    def __init__(self, c):
        self.c = c

    def matching_string(self, draw, state):
        return self.c

    def non_matching_string(self, draw, state):
        return draw(st.characters(blacklist_characters=self.c))

    def build_re(self):
        return "\\" + self.c

    @staticmethod
    def make(draw):
        # XXX many more escapes
        c = draw(st.sampled_from(special_characters))
        return Escape(c)


class Charset(Re):
    def __init__(self, elements):
        # either characters, or (start, stop) tuples
        self.elements = elements

    def matching_string(self, draw, state):
        x = draw(st.sampled_from(self.elements))
        if isinstance(x, tuple):
            return draw(st.characters(min_codepoint=ord(x[0]), max_codepoint=ord(x[1])))
        return x

    def non_matching_string(self, draw, state):
        if not any(isinstance(x, tuple) for x in self.elements):
            # easy case, only chars
            return draw(st.characters(blacklist_characters=self.elements))
        chars = "".join(x for x in self.elements if not isinstance(x, tuple))
        range_stops = [ord(x[1]) for x in self.elements if isinstance(x, tuple)]
        max_stop = max(range_stops)
        res = draw(
            st.characters(min_codepoint=max_stop + 1, blacklist_characters=chars)
        )
        return res

    def build_re(self):
        res = []
        for x in self.elements:
            if isinstance(x, tuple):
                res.append(f"{x[0]}-{x[1]}")
            else:
                res.append(x)
        return "[" + "".join(res) + "]"

    @staticmethod
    def make(draw):
        # XXX character classes
        elements = []
        for _ in range(draw(st.integers(min_value=2, max_value=20))):
            if draw(st.booleans()):
                # character
                elements.append(draw(st.characters(blacklist_characters="-^]\\")))
            else:
                # character range
                start = draw(st.characters(blacklist_characters="-^]\\"))
                stop = draw(
                    st.characters(
                        blacklist_characters="-^]\\", min_codepoint=ord(start) + 1
                    )
                )
                elements.append((start, stop))
        return Charset(elements)


class CharsetComplement(Re):
    def __init__(self, charset):
        assert isinstance(charset, Charset)
        self.charset = charset

    def matching_string(self, draw, state):
        return self.charset.non_matching_string(draw, state)

    def non_matching_string(self, draw, state):
        return self.charset.matching_string(draw, state)

    def build_re(self):
        charset = self.charset.build_re()
        assert charset.startswith("[")
        return f"[^{charset[1:-1]}]"

    @staticmethod
    def make(draw):
        return CharsetComplement(Charset.make(draw))


def re_simple(draw):
    cls = draw(
        st.sampled_from([Dot, Char, Escape, Charset, CharClass, CharsetComplement])
    )
    return cls.make(draw)


class RecursiveRe(Re):
    """ Abstract base class for "recursive" Re nodes, ie nodes that build on
    top of other nodes. """

    @classmethod
    def curry(cls, base):
        return lambda draw: cls.make_with_base(base, draw)

    @staticmethod
    def make_with_base(base, draw):
        raise NotImplementedError


class Repetition(RecursiveRe):
    istart = None
    istop = MAXREPEAT

    def __init__(self, base, lazy):
        self.base = base
        self.lazy = lazy

    def can_be_empty(self):
        return self.base.can_be_empty() or self.istart == 0

    def build_re(self):
        return self._build_re() + "?" * self.lazy

    def _build_re(self):
        raise NotImplementedError

    def matching_string(self, draw, state):
        repetition = draw(st.integers(min_value=self.istart, max_value=self.istop))
        res = [self.base.matching_string(draw, state) for i in range(repetition)]
        return "".join(res)

    def non_matching_string(self, draw, state):
        if self.can_be_empty() or self.base.can_be_empty():
            raise CantGenerateNonMatching
        res = [self.base.matching_string(draw, state) for i in range(self.istart)]
        non_matching_pos = draw(st.integers(min_value=0, max_value=len(res) - 1))
        res[non_matching_pos] = self.base.non_matching_string(draw, state)
        return "".join(res)

    @staticmethod
    def make_with_base(base, draw):
        b = base(draw)
        cls = draw(st.sampled_from([Star, Plus, FixedNum, StartStop, Start, Stop]))
        return cls.make_repetition(b, draw)


class Star(Repetition):
    istart = 0
    istop = MAXREPEAT

    def _build_re(self):
        return self.base.build_re() + "*"

    @staticmethod
    def make_repetition(base, draw):
        return Star(base, draw(st.booleans()))


class Plus(Repetition):
    istart = 1
    istop = MAXREPEAT

    def _build_re(self):
        return self.base.build_re() + "+"

    @staticmethod
    def make_repetition(base, draw):
        return Plus(base, draw(st.booleans()))


class FixedNum(Repetition):
    def __init__(self, base, num, lazy):
        Repetition.__init__(self, base, lazy)
        self.istart = self.istop = num

    def _build_re(self):
        return f"{self.base.build_re()}{{{self.istart}}}"

    @staticmethod
    def make_repetition(base, draw):
        num = draw(st.integers(min_value=0, max_value=MAXREPEAT))
        return FixedNum(base, num, draw(st.booleans()))


class StartStop(Repetition):
    def __init__(self, base, istart, istop, lazy):
        Repetition.__init__(self, base, lazy)
        self.istart = istart
        self.istop = istop

    def _build_re(self):
        return f"{self.base.build_re()}{{{self.istart},{self.istop}}}"

    @staticmethod
    def make_repetition(base, draw):
        start = draw(st.integers(min_value=0, max_value=MAXREPEAT))
        stop = draw(st.integers(min_value=start, max_value=MAXREPEAT))
        return StartStop(base, start, stop, draw(st.booleans()))


class Stop(Repetition):
    istart = 0

    def __init__(self, base, istop, lazy):
        Repetition.__init__(self, base, lazy)
        self.istop = istop

    def _build_re(self):
        return f"{self.base.build_re()}{{,{self.istop}}}"

    @staticmethod
    def make_repetition(base, draw):
        stop = draw(st.integers(min_value=0, max_value=MAXREPEAT))
        return Stop(base, stop, draw(st.booleans()))


class Start(Repetition):
    istop = MAXREPEAT

    def __init__(self, base, istart, lazy):
        Repetition.__init__(self, base, lazy)
        self.istart = istart

    def _build_re(self):
        return f"{self.base.build_re()}{{{self.istart},}}"

    @staticmethod
    def make_repetition(base, draw):
        start = draw(st.integers(min_value=0, max_value=MAXREPEAT))
        return Start(base, start, draw(st.booleans()))


class Sequence(RecursiveRe):
    def __init__(self, bases):
        self.bases = bases

    def can_be_empty(self):
        return all(base.can_be_empty() for base in self.bases)

    def matching_string(self, draw, state):
        return "".join(b.matching_string(draw, state) for b in self.bases)

    def non_matching_string(self, draw, state):
        if self.can_be_empty():
            raise CantGenerateNonMatching
        nonempty_positions = [
            i for (i, b) in enumerate(self.bases) if not b.can_be_empty()
        ]
        res = []
        for base_pos in nonempty_positions:
            res.append(self.bases[base_pos].non_matching_string(draw, state))
        return "".join(res)

    def build_re(self):
        return "".join(b.build_re() for b in self.bases)

    @staticmethod
    def make_with_base(base, draw):
        return Sequence(
            [
                base(draw)
                for i in range(draw(st.integers(min_value=2, max_value=MAXREPEAT)))
            ]
        )


class SequenceWithBackref(Sequence):
    @staticmethod
    def make_with_base(base, draw):
        bases = [
            base(draw)
            for i in range(draw(st.integers(min_value=2, max_value=MAXREPEAT)))
        ]
        if IS_PYPY and sys.pypy_version_info < (7, 3, 1):
            # PyPy before 7.3.1 actually has broken group references!
            return Sequence(bases)
        # the following code would have found the bug in
        # https://foss.heptapod.net/pypy/pypy/commit/c83c263f9f00d18d48ef536947c9b61ca53e01a2
        group = draw(st.integers(min_value=0, max_value=len(bases) - 1))
        name = gensym()
        bases[group] = g = NamedGroup(bases[group], name)
        bases.append(GroupReference(g))
        return Sequence(bases)


class NamedGroup(Re):
    def __init__(self, base, name):
        self.base = base
        self.name = name

    def can_be_empty(self):
        return self.base.can_be_empty()

    def build_re(self):
        return f"(?P<{self.name}>{self.base.build_re()})"

    def matching_string(self, draw, state):
        res = self.base.matching_string(draw, state)
        state.groups[self] = res
        return res

    def non_matching_string(self, draw, state):
        res = self.base.non_matching_string(draw, state)
        state.groups[self] = res
        return res


class GroupReference(Re):
    def __init__(self, group):
        self.group = group

    def can_be_empty(self):
        return self.group.can_be_empty()

    def build_re(self):
        return f"(?P={self.group.name})"

    def matching_string(self, draw, state):
        return state.groups[self.group]

    def non_matching_string(self, draw, state):
        return state.groups[self.group]  # doesn't matter, the group can't match


class Disjunction(RecursiveRe):
    def __init__(self, bases):
        self.bases = bases

    def can_be_empty(self):
        return any(base.can_be_empty() for base in self.bases)

    def matching_string(self, draw, state):
        base = draw(st.sampled_from(self.bases))
        return base.matching_string(draw, state)

    def non_matching_string(self, draw, state):
        raise CantGenerateNonMatching

    def build_re(self):
        return "|".join(b.build_re() for b in self.bases)

    @staticmethod
    def make_with_base(base, draw):
        return Disjunction(
            [
                base(draw)
                for i in range(draw(st.integers(min_value=2, max_value=MAXREPEAT)))
            ]
        )


# run some tests


def re_test(maker):
    @given(data=st.data())
    def test(self, data):
        draw = data.draw
        re_object = maker(draw)
        re_pattern = re_object.build_re()
        syes = re_object.matching_string(draw, State())
        compiled = re.compile(re_pattern)
        t1 = time.time()
        self.assertIsNotNone(compiled.match(syes))
        t2 = time.time()
        # potentially brittle, but, try to find accidentally slow things
        # eg quadratic algorithms
        # on the machine this was developed, matching was at least 500x faster
        # always
        self.assertLessEqual(t2 - t1, 0.01)
        try:
            sno = re_object.non_matching_string(draw, State())
        except CantGenerateNonMatching:
            pass
        else:
            t1 = time.time()
            self.assertIsNone(compiled.match(sno))
            t2 = time.time()
            self.assertLessEqual(t2 - t1, 0.01)

    return test


class TestRe(unittest.TestCase):
    test_char = re_test(Char.make)
    test_dots = re_test(Dot.make)
    test_escape = re_test(Escape.make)
    test_charclass = re_test(CharClass.make)
    test_charset = re_test(Charset.make)
    test_simple = re_test(re_simple)

    simple_repetition = Repetition.curry(re_simple)
    test_simple_repetition = re_test(simple_repetition)

    sequence_repetition = Sequence.curry(simple_repetition)
    test_sequence_repetition = re_test(sequence_repetition)

    backref_sequence = SequenceWithBackref.curry(simple_repetition)
    test_backref_sequence = re_test(backref_sequence)

    test_simple_disjunction = re_test(Disjunction.curry(re_simple))

    disjunction_sequence_repetition = Disjunction.curry(backref_sequence)
    test_disjunction_sequence_repetition = re_test(disjunction_sequence_repetition)