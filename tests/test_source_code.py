import ast
import dis
import io
import tokenize
import unittest

import hypothesmith
from hypothesis import HealthCheck, example, given, reject, settings, strategies as st

# Used to mark tests which generate arbitrary source code,
# because that's a relatively expensive thing to get right.
settings.register_profile(
    "slow", deadline=None, suppress_health_check=HealthCheck.all(),
)


class TestAST(unittest.TestCase):
    @unittest.skipIf(not hasattr(ast, "unparse"), reason="new in 3.9")
    @given(source_code=hypothesmith.from_grammar())
    @settings.get_profile("slow")
    def test_ast_unparse(self, source_code):
        """Unparsing always produces code which parses back to the same ast."""
        first = ast.parse(source_code)
        unparsed = ast.unparse(first)
        second = ast.parse(unparsed)
        assert ast.dump(first) == ast.dump(second)


class TestDis(unittest.TestCase):
    @given(
        code_object=hypothesmith.from_grammar().map(
            lambda s: compile(s, "<string>", "exec")
        ),
        first_line=st.none() | st.integers(0, 100),
        current_offset=st.none() | st.integers(0, 100),
    )
    @settings.get_profile("slow")
    def test_disassembly(self, code_object, first_line, current_offset):
        """Exercise the dis module."""
        # TODO: what other properties of this module should we test?
        bcode = dis.Bytecode(
            code_object, first_line=first_line, current_offset=current_offset
        )
        self.assertIs(code_object, bcode.codeobj)
        for inst in bcode:
            self.assertIsInstance(inst, dis.Instruction)


class TestLib2to3(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/2to3.html
    pass


def fixup(s):
    """Avoid known issues with tokenize() by editing the string."""
    return "".join(x for x in s if x.isprintable()).strip().strip("\\").strip() + "\n"


class TestTokenize(unittest.TestCase):
    """Tests that the result of `untokenize` round-trips back to the same token stream,
    per https://docs.python.org/3/library/tokenize.html#tokenize.untokenize

    Unfortunately these tests demonstrate that it doesn't, and thus we have
    `@unittest.expectedFailure` decorators.
    """

    @unittest.expectedFailure
    @example("#")
    @example("\n\\\n")
    @example("#\n\x0cpass#\n")
    @given(source_code=hypothesmith.from_grammar().map(fixup).filter(str.strip))
    @settings.get_profile("slow")
    def test_tokenize_round_trip_bytes(self, source_code):
        try:
            source = source_code.encode("utf-8-sig")
        except UnicodeEncodeError:
            reject()
        tokens = list(tokenize.tokenize(io.BytesIO(source).readline))
        # `outbytes` may have changed whitespace from `source`
        outbytes = tokenize.untokenize(tokens)
        output = list(tokenize.tokenize(io.BytesIO(outbytes).readline))
        self.assertEqual(
            [(tt.type, tt.string) for tt in tokens],
            [(ot.type, ot.string) for ot in output],
        )
        # It would be nice if the round-tripped string stabilised...
        # self.assertEqual(outbytes, tokenize.untokenize(output))

    @unittest.expectedFailure
    @example("#")
    @example("\n\\\n")
    @example("#\n\x0cpass#\n")
    @given(source_code=hypothesmith.from_grammar().map(fixup).filter(str.strip))
    @settings.get_profile("slow")
    def test_tokenize_round_trip_string(self, source_code):
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        # `outstring` may have changed whitespace from `source_code`
        outstring = tokenize.untokenize(tokens)
        output = tokenize.generate_tokens(io.StringIO(outstring).readline)
        self.assertEqual(
            [(tt.type, tt.string) for tt in tokens],
            [(ot.type, ot.string) for ot in output],
        )
        # It would be nice if the round-tripped string stabilised...
        # self.assertEqual(outstring, tokenize.untokenize(output))
