import pytest
from eucy import modify
import random


def _test_modify_doc(eudoc, eu_wrapper, nlp):
    """Test general in and output of modify.modify_doc()."""

    eudoc_mod = modify.modify_doc(eudoc)

    assert type(eudoc_mod) == type(eudoc), 'modify_doc() did not return the same type of object as input.'

    # run through eu_wrapper
    eudoc_mod = eu_wrapper(eudoc_mod)

    assert type(eudoc_mod) == type(eudoc), 'modify_doc() did not return the same type of object as input after running through eu_wrapper.'

    # try with nlp
    eudoc_mod = modify.modify_doc(eudoc, nlp=nlp)

    assert type(eudoc_mod) == type(eudoc), 'modify_doc() did not return the same type of object as input when nlp was passed.'

    # run through eu_wrapper
    eudoc_mod = eu_wrapper(eudoc_mod)


def _test_modify_doc_replacement(eudoc, eu_wrapper):
    """Test modify.modify_doc() for replacement of a random citation, recital, and article."""

    # replace a random citation, recital, and article
    if len(eudoc.spans['citations']) > 0:
        random_citation_i = random.choice(range(len(eudoc.spans['citations'])))
        eudoc.spans['citations'][random_citation_i] = modify.replace_text(eudoc.spans['citations'][random_citation_i], 'This is a test.')

    if len(eudoc.spans['recitals']) > 0:
        random_recital_i = random.choice(range(len(eudoc.spans['recitals'])))
        eudoc.spans['recitals'][random_recital_i] = modify.replace_text(eudoc.spans['recitals'][random_recital_i], 'This is a test.')

    if len(eudoc.spans['articles']) > 0:
        random_article_i = random.choice(range(len(eudoc.spans['articles'])))
        eudoc.spans['articles'][random_article_i] = modify.replace_text(eudoc.spans['articles'][random_article_i], 'This is a test.')

    eudoc_mod = modify.modify_doc(eudoc)

    assert eudoc_mod.spans['citations'][random_citation_i].text.strip() == 'This is a test.', 'Citation replacement failed.'
    assert eudoc_mod.spans['recitals'][random_recital_i].text.strip() == 'This is a test.', 'Recital replacement failed.'
    assert eudoc_mod.spans['articles'][random_article_i].text.strip() == 'This is a test.', 'Article replacement failed.'

    # run through eu_wrapper
    eudoc_mod = eu_wrapper(eudoc_mod)


def test_modify_doc_deletion(eudoc, eu_wrapper):
    """Test modify.modify_doc() for deletion of a random citation, recital, and article."""

    # delete a random citation, recital, and article
    if len(eudoc.spans['citations']) > 0:
        random_citation_i = random.choice(range(len(eudoc.spans['citations'])))
        eudoc.spans['citations'][random_citation_i] = modify.delete_text(eudoc.spans['citations'][random_citation_i])

    if len(eudoc.spans['recitals']) > 0:
        random_recital_i = random.choice(range(len(eudoc.spans['recitals'])))
        eudoc.spans['recitals'][random_recital_i] = modify.delete_text(eudoc.spans['recitals'][random_recital_i])

    if len(eudoc.spans['articles']) > 0:
        random_article_i = random.choice(range(len(eudoc.spans['articles'])))
        eudoc.spans['articles'][random_article_i] = modify.delete_text(eudoc.spans['articles'][random_article_i])

    eudoc_mod = modify.modify_doc(eudoc)

    # @TODO delete this once this is implemented in modify_text()
    # @TODO this breaks some stats, e.g. 51995PC0034(11)
    eudoc_mod = eu_wrapper(eudoc_mod)

    assert len(eudoc_mod.spans['citations']) == len(eudoc.spans['citations']) - 1, 'Citation deletion failed.'
    #assert eudoc_mod._.complexity['citations'] == eudoc._.complexity['citations'] -1, 'Citation deletion failed.'

    assert len(eudoc_mod.spans['recitals']) == len(eudoc.spans['recitals']) - 1, 'Recital deletion failed.'
    #assert eudoc_mod._.complexity['recitals'] == eudoc._.complexity['recitals'] -1, 'Recital deletion failed.'

    assert len(eudoc_mod.spans['articles']) == len(eudoc.spans['articles']) - 1, 'Article deletion failed.'
    #assert eudoc_mod._.complexity['articles'] == eudoc._.complexity['articles'] -1, 'Article deletion failed.'

    # run through eu_wrapper
    eudoc_mod = eu_wrapper(eudoc_mod)

