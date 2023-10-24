#!/usr/bin/env python
"""Tests for `euCy` package to ensure annotation of individial parts and elements works."""
# pylint: disable=redefined-outer-name

import krippendorff
import numpy as np
import pytest

from .conftest import result_by_id

# TESTS

request_celex_id = lambda request: request.node.callspec.params['html']


def _test_object_creation(eu_wrapper, eudoc, text):
    """Test EuWrapper object creation via doc and via string"""

    eudoc_str = eu_wrapper(text)

    assert eudoc._.complexity == eudoc_str._.complexity


# TESTS: Individual documents


def test_citations(eudoc, results, request):
    """Test number of citations detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['citations'] == pytest.approx(result_by_id(
        celex_id, results)['citations'],
                                                            abs=0)


def test_recitals(eudoc, results, request):
    """Test number of recitals detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['recitals'] == pytest.approx(result_by_id(
        celex_id, results)['recitals'],
                                                           abs=0)


def test_articles(eudoc, results, request):
    """Test number of articles detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['articles'] == pytest.approx(result_by_id(
        celex_id, results)['articles'],
                                                           abs=0)


def test_references_internal(eudoc, results, request):
    """Test number of internal references detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['references']['internal'] == pytest.approx(
        result_by_id(celex_id, results)['ref_int_enacting'], abs=3)


def test_references_external(eudoc, results, request):
    """Test number of external references detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['references']['external'] == pytest.approx(
        result_by_id(celex_id, results)['ref_ext_enacting'], abs=3)


def test_references_total(eudoc, results, request):
    """Test number of total references detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['references']['internal'] + eudoc._.complexity[
        'references']['external'] == pytest.approx(result_by_id(
            celex_id, results)['ref_enacting'],
                                                   abs=3)


# Inter-coder reliability tests


# ICR: Recitals
@pytest.mark.parametrize("scale", ['interval', 'nominal', 'ordinal'])
@pytest.mark.parametrize("var", [
    'citations', 'recitals', 'articles', 'ref_int_enacting',
    'ref_ext_enacting', 'ref_enacting'
])
def test_icr(eudocs, results, var, scale, euplex_alphas):
    """Test Inter-coder reliability for recitals (krippendorff's alpha) between euCy and hand-annotated results"""

    # @TODO possibly only consider documents that are also in the original dataset vs hand-coded data ICR calculation

    if var in ['citations', 'recitals', 'articles']:
        results_array = np.array([
            results['doc_proposal_' + var],
            [eudoc._.complexity[var] for eudoc in eudocs]
        ])
    elif var == 'ref_int_enacting':
        results_array = np.array([
            results['doc_proposal_' + var],
            [eudoc._.complexity['references']['internal'] for eudoc in eudocs]
        ])
    elif var == 'ref_ext_enacting':
        results_array = np.array([
            results['doc_proposal_' + var],
            [eudoc._.complexity['references']['external'] for eudoc in eudocs]
        ])
    elif var == 'ref_enacting':
        results_array = np.array([
            results['doc_proposal_' + var],
            [
                eudoc._.complexity['references']['internal'] +
                eudoc._.complexity['references']['external']
                for eudoc in eudocs
            ]
        ])

    alphas = {}

    alpha = krippendorff.alpha(reliability_data=results_array,
                               level_of_measurement=scale)

    # compare alphas
    assert alpha >= euplex_alphas[var][scale]
