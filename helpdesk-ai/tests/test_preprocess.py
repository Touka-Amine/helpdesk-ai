"""Basic tests for preprocessing utilities."""

from src.data.preprocess import basic_clean


def test_basic_clean():
    assert basic_clean("Hello   World") == "hello world"
