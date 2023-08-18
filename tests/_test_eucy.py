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

# @TODO step A: read this https://py-pkgs.org/05-testing.html


# @TODO step B
# Test basic functionality
# @TODO: test object creation
# @TODO: test parsing
# @TODO: test annotation


# @TOOD step C: unit tests?


# FIXTURES

@pytest.fixture
def nlp_empty():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """

    nlp = spacy.blank("en")

    return nlp


@pytest.fixture
def nlp_en_web_core_sm():

    import en_core_web_sm

    nlp = en_core_web_sm.load()

    return nlp



def get_sample_texts():

    # read in texts
    sample_texts_html = {}

    for f in os.listdir('data/proposals'):
        with open('data/proposals/' + f, 'r') as p:
            sample_texts_html[f.replace('.html', '')] = p.read()

    sample_texts = {celex: utils.text_from_html(html) for celex, html in sample_texts_html.items()}

    return sample_texts

@pytest.fixture
def sample_texts(request):
    return get_sample_texts()

def get_sample_texts_results():

    # read in hand-annotated results
    results = pd.read_csv('data/hhk_reliability.csv')

    return results



@pytest.fixture
def sample_texts_results(request):
    return get_sample_texts_results()

def get_sample_texts_results_celex_ids():
    # read in hand-annotated results
    results = get_sample_texts_results()

    return results['celex_id'].tolist()



# @pytest.fixture
# def docs_empty(nlp_empty, sample_texts):
#
#     docs = {}
#
#     for celex, text in sample_texts.items():
#         doc = nlp_empty(text)
#         docs[celex] = doc
#
#     return docs
#
# @pytest.fixture
# def docs_en_web_core_sm(nlp_en_web_core_sm, sample_texts):
#
#     docs = {}
#
#     for celex, text in sample_texts.items():
#         doc = nlp_en_web_core_sm(text)
#         docs[celex] = doc
#
#     return docs

@pytest.fixture
def eu_wrapper_empty(nlp_empty):

    return EuWrapper(nlp_empty, debug=False)

@pytest.fixture
def eu_wrapper_en_web_core_sm(nlp_en_web_core_sm):

    return EuWrapper(nlp_en_web_core_sm, debug=False)


def create_objects_doc(nlp, eu_wrapper, sample_texts):

    docs = {}

    for celex, text in sample_texts.items():
        doc = nlp(text)
        docs[celex] = eu_wrapper(doc)

    return docs

def create_objects_str(eu_wrapper, sample_texts):

    docs = {}

    for celex, text in sample_texts.items():
        docs[celex] = eu_wrapper(text)

    return docs

@pytest.fixture
def eudocs_doc_empty(nlp_empty, eu_wrapper_empty, sample_texts):
    return create_objects_doc(nlp_empty, eu_wrapper_empty, sample_texts)

@pytest.fixture
def eudocs_str_empty(eu_wrapper_empty, sample_texts):
    return create_objects_str(eu_wrapper_empty, sample_texts)

# testing whether two different object creation methods yield identical results
@pytest.mark.parametrize('eudocs_doc,eudocs_str', [('eudocs_doc_empty','eudocs_str_empty')])
def test_object_creation(eudocs_doc, eudocs_str, request):

    eudocs_doc = request.getfixturevalue(eudocs_doc)
    eudocs_str = request.getfixturevalue(eudocs_str)

    eudocs_doc_complexity = [eudoc._.complexity for eudoc in eudocs_doc.values()]
    eudocs_str_complexity = [eudoc._.complexity for eudoc in eudocs_str.values()]

    assert eudocs_doc_complexity == eudocs_str_complexity, "eudoc objects created from doc and text string are not identical"




def get_results_by_celex_id(results, celex_id):

    res = results[results['celex_id'] == celex_id]

    assert len(res) == 1, "more than one result for celex_id {}".format(celex_id)

    res = res.to_dict()

    # make into a flat dict
    res = {k.replace('doc_proposal_',''): [(ke, va) for ke, va in v.items()][0][1] for k, v in res.items()}

    return res



@pytest.mark.parametrize('celex_id', [celex_id for celex_id in get_sample_texts_results_celex_ids()])
@pytest.mark.parametrize('eudocs', [lazy_fixture(eudoc) for eudoc in ['eudocs_doc_empty']])
def test_citations(celex_id, eudocs_doc_empty, sample_texts_results):

    # get eudoc by celex_id
    eudoc = eudocs_doc_empty[celex_id]

    # get hand-coding result
    res_hc = get_results_by_celex_id(sample_texts_results, celex_id)

    # compare citations
    assert eudoc._.complexity['citations'] == pytest.approx(res_hc['citations'], rel=0.2, abs=5), "citations do not match for celex_id {}".format(celex_id)


#
# @pytest.mark.parametrize('celex_id,text', [(celex_id, doc) for celex_id, doc in get_sample_texts().items()], ids=lambda x: str(x)[:10])
# @pytest.mark.parametrize('nlp,eu_wrapper', [('nlp_empty','eu_wrapper_empty')])
# def test_element_detection(nlp, eu_wrapper, celex_id, text, sample_texts_results, request):
#
#     # make sure the celex_id is in the results
#     try:
#         assert celex_id in sample_texts_results['celex_id'].values, "celex_id {} not in results".format(celex_id)
#     except AssertionError as e:
#         return
#
#
#     # get nlp/wrapper objects
#     nlp = request.getfixturevalue(nlp)
#     eu_wrapper = request.getfixturevalue(eu_wrapper)
#
#     # create object
#
#     # @TODO hier weiter: why does this fail with Attribute Error? Recreate outside of tests to see what's going on
#
#     try:
#         doc = nlp(text)
#         eudoc_doc = eu_wrapper(doc)
#         assert True
#     except:
#         assert False, "Error creating eudoc from doc object"
#
#     try:
#         eudoc_str = eu_wrapper(text)
#         assert True
#     except:
#         assert False, "Error creating eudoc from text string"
#
#     assert eudoc_doc._.complexity == eudoc_str._.complexity, "eudoc objects created from doc and text string are not identical"
#
#     # test element detection relibaility
#
#     results_hc = sample_texts_results[sample_texts_results['celex_id'] == celex_id]
#
#     # make sure we have only one result
#     assert len(results_hc) == 1, "More than one result for celex_id {}".format(celex_id)
#
#     results_hc = results_hc.to_dict()
#
#     # make into a flat dict
#     results_hc = {k.replace('doc_proposal_',''): [(ke, va) for ke, va in v.items()][0][1] for k, v in results_hc.items()}
#
#     assertions_errors = []
#
#     ## match (pytest.approx)
#     try:
#         assert eudoc_doc._.complexity['citations'] == pytest.approx(results_hc['citations'], 0.1, abs=2), "citations not matching"
#     except AssertionError as e:
#         print(e)
#         assertions_errors.append(e)
#
#     try:
#         assert eudoc_doc._.complexity['recitals'] == pytest.approx(results_hc['recitals'], 0.1, abs=2), "recitals not matching"
#     except AssertionError as e:
#         print(e)
#         assertions_errors.append(e)
#
#     try:
#         assert eudoc_doc._.complexity['articles'] == pytest.approx(results_hc['articles'], 0.1, abs=2), "articles not matching"
#     except AssertionError as e:
#         print(e)
#         assertions_errors.append(e)
#
#     try:
#         assert eudoc_doc._.complexity['references']['internal'] == pytest.approx(results_hc['ref_int_enacting'], 0.3), "internal references not matching"
#     except AssertionError as e:
#         print(e)
#         assertions_errors.append(e)
#
#     try:
#         assert eudoc_doc._.complexity['references']['external'] == pytest.approx(results_hc['ref_ext_enacting'], 0.3), "external references not matching"
#     except AssertionError as e:
#         print(e)
#         assertions_errors.append(e)
#
#     try:
#         assert eudoc_doc._.complexity['references']['internal'] + eudoc_doc._.complexity['references']['external'] == pytest.approx(results_hc['ref_enacting'], 0.3), "total references not matching"
#     except AssertionError as e:
#         print(e)
#         assertions_errors.append(e)
#
#
#     if len(assertions_errors) > 0:
#         raise AssertionError(assertions_errors)
#
#
#
# # @TODO test ICR (aggregate comparison)
