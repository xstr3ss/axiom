import pytest
from text_formatter import format_text


class TestValidation:
    def test_non_string_text_raises_type_error(self):
        with pytest.raises(TypeError, match="text must be a string"):
            format_text(123)

    def test_none_text_raises_type_error(self):
        with pytest.raises(TypeError, match="text must be a string"):
            format_text(None)

    def test_non_int_line_length_raises_type_error(self):
        with pytest.raises(TypeError, match="line_length must be an integer or None"):
            format_text("hello", line_length="10")

    def test_bool_line_length_raises_type_error(self):
        with pytest.raises(TypeError, match="line_length must be an integer or None"):
            format_text("hello", line_length=True)

    def test_negative_line_length_raises_value_error(self):
        with pytest.raises(ValueError, match="line_length must be >= 1"):
            format_text("hello", line_length=-1)

    def test_zero_line_length_raises_value_error(self):
        with pytest.raises(ValueError, match="line_length must be >= 1"):
            format_text("hello", line_length=0)


class TestWhitespaceHandling:
    def test_leading_trailing_whitespace_removed(self):
        assert format_text("  hello world  ") == "hello world"

    def test_internal_whitespace_collapsed(self):
        assert format_text("hello   world") == "hello world"

    def test_mixed_whitespace_collapsed(self):
        assert format_text("hello\t\t\nworld") == "hello world"

    def test_empty_string(self):
        assert format_text("") == ""

    def test_whitespace_only_string(self):
        assert format_text("   ") == ""


class TestLineWrapping:
    def test_no_wrapping_by_default(self):
        result = format_text("hello world this is a long text")
        assert result == "hello world this is a long text"

    def test_wrapping_at_exact_boundary(self):
        # "hello" (5) + " " (1) + "world" (5) = 11 > 10
        # So "hello world" should wrap if line_length is 10
        result = format_text("hello world", line_length=10)
        assert result == "hello\nworld"

    def test_wrapping_with_exact_fit(self):
        # "hi" (2) + " " (1) + "there" (5) = 8 <= 8
        result = format_text("hi there", line_length=8)
        assert result == "hi there"

    def test_wrapping_multiple_lines(self):
        # words: "one", "two", "three"
        # line 1: "one two" (7 chars)
        # line 2: "three" (5 chars)
        result = format_text("one two three", line_length=7)
        assert result == "one two\nthree"

    def test_wrapping_single_long_word(self):
        # "longword" is 8 chars. line_length 5.
        # Cannot split words per implementation.
        result = format_text("longword", line_length=5)
        assert result == "longword"
        
    def test_wrapping_exact_line_length(self):
        # "hello" is 5 chars. line_length 5.
        result = format_text("hello world", line_length=5)
        assert result == "hello\nworld"

    def test_wrapping_preserves_separation(self):
        result = format_text("a b c", line_length=3)
        # "a b" (3) -> "a b"
        # "c" -> "c"
        assert result == "a b\nc"


class TestUppercase:
    def test_uppercase_without_wrapping(self):
        result = format_text("hello world", uppercase=True)
        assert result == "HELLO WORLD"

    def test_uppercase_with_wrapping(self):
        result = format_text("hello world", line_length=5, uppercase=True)
        assert result == "HELLO\nWORLD"

    def test_uppercase_default_false(self):
        result = format_text("Hello World")
        assert result == "Hello World"

    def test_uppercase_preserves_existing_case(self):
        # If input is already uppercase, it stays uppercase
        result = format_text("HELLO", uppercase=True)
        assert result == "HELLO"

    def test_uppercase_converts_mixed_case(self):
        result = format_text("HeLLo WoRlD", uppercase=True)
        assert result == "HELLO WORLD"


class TestCombinedFunctionality:
    def test_strip_wrap_uppercase(self):
        input_str = "  Mix   case   example  "
        # Strip: "Mix case example"
        # Wrap (line_length=6): 
        # "Mix" (3)
        # "case" (4) -> "Mix case" is 8 > 6. So "Mix", then "case"
        # "example" (7) > 6. So "case", "example"
        # Lines: "Mix", "case example" (12 > 6)? No.
        # Let's trace:
        # words: "Mix", "case", "example"
        # line = "Mix" (3)
        # next "case": 3+1+4 = 8 > 6. Append "Mix", start "case"
        # next "example": 4+1+7 = 12 > 6. Append "case", start "example"
        # End. Append "example"
        # Result lines: "Mix", "case", "example"
        # Join: "Mix\ncase\nexample"
        # Uppercase: "MIX\ncASE\nEXAMPLE"
        
        result = format_text(input_str, line_length=6, uppercase=True)
        assert result == "MIX\nCASE\nEXAMPLE"
        
    def test_doctest_example_1(self):
        assert format_text("  hello   world  ") == 'hello world'

    def test_doctest_example_2(self):
        assert format_text("hello world", line_length=5) == 'hello\nworld'

    def test_doctest_example_3(self):
        assert format_text("hello world", uppercase=True) == 'HELLO WORLD'

    def test_doctest_example_4(self):
        # "HELLO   World" -> "HELLO World"
        # Wrap length 7:
        # "HELLO" (5), "World" (5)
        # 5+1+5 = 11 > 7
        # So "HELLO", "World"
        # Uppercase: "HELLO", "WORLD"
        assert format_text("HELLO   World", line_length=7, uppercase=True) == 'HELLO\nWORLD'

    def test_return_type_is_string(self):
        result = format_text("test")
        assert isinstance(result, str)
