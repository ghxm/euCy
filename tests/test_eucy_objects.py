#!/usr/bin/env python
"""Tests for `euCy` package."""
# pylint: disable=redefined-outer-name

import pytest
from .conftest import result_by_id



# TESTS

request_celex_id = lambda request: request.node.callspec.params['html']

def _test_object_creation(eu_wrapper, eudoc, text):
    """Test EuWrapper object creation via doc and via string"""

    eudoc_str = eu_wrapper(text)

    assert eudoc._.complexity == eudoc_str._.complexity


# TESTS: Aggregated documents

def _test_aggregate(eudocs, results):

    """Test Inter-coder reliability"""


    print('')

    # @TODO ICR overall high enough?

    pass

# TESTS: Individual documents

# @TODO set approx limits from hand coding differences and investigate when the code might have been changed :o

def test_citations(eudoc, results, request):
    """Test number of citations detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['citations'] == pytest.approx(result_by_id(celex_id, results)['citations'], abs=0)

def test_recitals(eudoc, results, request):
    """Test number of recitals detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['recitals'] == pytest.approx(result_by_id(celex_id, results)['recitals'], abs=0)

def test_articles(eudoc, results, request):

    """Test number of articles detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['articles'] == pytest.approx(result_by_id(celex_id, results)['articles'],  abs=0)

def test_references_internal(eudoc, results, request):

        """Test number of internal references detection"""

        celex_id = request_celex_id(request)

        assert eudoc._.complexity['references']['internal'] == pytest.approx(result_by_id(celex_id, results)['ref_int_enacting'], abs=3)


def test_references_external(eudoc, results, request):

        """Test number of external references detection"""

        celex_id = request_celex_id(request)

        assert eudoc._.complexity['references']['external'] == pytest.approx(result_by_id(celex_id, results)['ref_ext_enacting'], abs=3)

def test_references_total(eudoc, results, request):

    """Test number of total references detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['references']['internal'] + eudoc._.complexity['references']['external'] == pytest.approx(result_by_id(celex_id, results)['ref_enacting'], abs=3)



