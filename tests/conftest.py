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

    # make corrections
    results.loc[results['celex_id'] == '52011PC0654', 'doc_proposal_articles'] = 12
    results.loc[results['celex_id'] == '52007PC0491', 'doc_proposal_recitals'] = 7

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
def eudocs(nlp, eu_wrapper):
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



@pytest.fixture
def euplex_dataset_results(results):
    """Read in euplex dataset"""

    # download euplex dataset and read in
    euplex = pd.read_csv('data/euplex_dataset_results.csv') # read in subset of jan 2023 version

    return euplex



@pytest.fixture
def euplex_alphas():
    """ ICR results from the euplex dataset paper """


    # krippendorrf's alphas from paper annex
    return {
        'citations': {
            'nominal': 0.974,
            'ordinal': 0.994,
            'interval': 0.984
        },
        'recitals': {
            'nominal': 0.927,
            'ordinal': 0.944,
            'interval': 0.917
        },
        'articles': {
            'nominal': 0.954,
            'ordinal': 0.995,
            'interval': 0.999
        },
        'ref_int_enacting': {
            'nominal': 0.373,
            'ordinal': 0.797,
            'interval': 0.861
        },
        'ref_ext_enacting': {
            'nominal': 0.450,
            'ordinal': 0.909,
            'interval': 0.861
        },
        'ref_enacting': {
            'nominal': 0.388,
            'ordinal': 0.904,
            'interval': 0.977
        }

    }
