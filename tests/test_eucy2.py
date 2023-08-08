#!/usr/bin/env python
"""Tests for `euCy` package."""
# pylint: disable=redefined-outer-name

import pytest
from pytest_lazyfixture import lazy_fixture

import spacy
import os
from eucy import utils
from eucy.eucy import EuWrapper
import pandas as pd


# FIXTURES

def get_results():
    """Read in hand-annotated results"""

    results = pd.read_csv('data/hhk_reliability.csv')

    return results

cases_celex_ids = get_results()['celex_id'].unique()
html_dir = os.listdir('data/proposals')

@pytest.fixture
def results():
    """Hand-annotated results fixture"""

    results = get_results()

    return results

def result_by_id(celex_id, results = None):
    """Hand-annotated results fixture"""

    if results is None:
        results = get_results()

    result = results[results['celex_id'] == celex_id]

    assert len(result) == 1, "more than one result for celex_id {}".format(celex_id)

    res = result.to_dict()

    res = {k.replace('doc_proposal_',''): [(ke, va) for ke, va in v.items()][0][1] for k, v in res.items()}

    return res


#@pytest.fixture(params=['blank','en_core_web_sm'])
@pytest.fixture(params=['blank'])
def nlp(request):
    """spaCy model fixture"""

    if request.param == 'blank':
        nlp = spacy.blank("en")
    elif request.param == 'en_core_web_sm':
        import en_core_web_sm
        nlp = en_core_web_sm.load()

    return nlp

@pytest.fixture
def eu_wrapper(nlp):
    """euCy wrapper fixture"""

    eu_wrapper = EuWrapper(nlp)

    return eu_wrapper



@pytest.fixture(params=cases_celex_ids)
def html(request):
    """Sample text html fixture"""

    with open('data/proposals/' + request.param + '.html', 'r') as p:
        sample_text_html = p.read()

    return sample_text_html

@pytest.fixture
def text(html):
    """Sample text fixture"""

    text = utils.text_from_html(html)

    return text
@pytest.fixture
def eu_wrapper(nlp):
    """euCy wrapper fixture"""

    eu_wrapper = EuWrapper(nlp)

    return eu_wrapper

@pytest.fixture
def eudoc(nlp, eu_wrapper, text):
    """spaCy doc fixture"""

    doc = nlp(text)
    eudoc = eu_wrapper(doc)

    return eudoc

@pytest.fixture
def eudocs(nlp, eu_wrapper, text):
    """spaCy docs fixture"""

    htmls = []

    for id in cases_celex_ids:

        with open('data/proposals/' + id + '.html', 'r') as p:
            sample_text_html = p.read()

        htmls.append(sample_text_html)

    texts = [utils.text_from_html(html) for html in htmls]

    docs = [nlp(text) for text in texts]

    eudocs = [eu_wrapper(doc) for doc in docs]

    return eudocs


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

    assert eudoc._.complexity['citations'] == pytest.approx(result_by_id(celex_id, results)['citations'], 0.05, 1)

def test_recitals(eudoc, results, request):
    """Test number of recitals detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['recitals'] == pytest.approx(result_by_id(celex_id, results)['recitals'], 0.05, 1)

def test_articles(eudoc, results, request):

    """Test number of articles detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['articles'] == pytest.approx(result_by_id(celex_id, results)['articles'], 0.2, 5)

def test_references_internal(eudoc, results, request):

        """Test number of internal references detection"""

        celex_id = request_celex_id(request)

        assert eudoc._.complexity['references']['internal'] == pytest.approx(result_by_id(celex_id, results)['ref_int_enacting'], 0.3, 8)


def test_references_external(eudoc, results, request):

        """Test number of external references detection"""

        celex_id = request_celex_id(request)

        assert eudoc._.complexity['references']['external'] == pytest.approx(result_by_id(celex_id, results)['ref_ext_enacting'], 0.3, 8)

def test_references_total(eudoc, results, request):

    """Test number of total references detection"""

    celex_id = request_celex_id(request)

    assert eudoc._.complexity['references']['internal'] + eudoc._.complexity['references']['external'] == pytest.approx(result_by_id(celex_id, results)['ref_enacting'], 0.3, 8)



