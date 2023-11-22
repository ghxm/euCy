#!/usr/bin/env python
"""Tests for `euCy` package to ensure modification of documents and elements works."""
# pylint: disable=redefined-outer-name

import random
from eucy import modify
from eucy import utils
import spacy


def get_article_text():
    return """

Article 1

For the 1995/96 marketing year, the aid provided for in Article 4 of Regulation (EEC)  No 1308/70 shall be:

a)  as regards flax: ECU 935,65/ha;

b)  as regards hemp: ECU 774,79/ha.

"""

def get_test_article():

    article = spacy.blank("en")(get_article_text())

    utils.set_extensions(article)

    return article


def get_test_article_elements(article):

    # create article element spans
    article_elements = {
        'pars': [article.char_span(13, 194)],
        'subpars': [[article.char_span(13, 194)]],
        'points': [[[article.char_span(122, 159), article.char_span(159, 194)]]],
        'indents': [[[]]]
    }

    return article_elements

def clear_article_element_spans(article_elements):

    for p_i, p in enumerate(article_elements['pars']):
        p._.delete()
        for s_i, s in enumerate(article_elements['subpars'][p_i]):
            s._.delete()
            for i_i, i in enumerate(article_elements['indents'][p_i][s_i]):
                i._.delete()
            for p_i, p in enumerate(article_elements['points'][p_i][s_i]):
                p._.delete()

def test_article_element_modification():

    article_text = get_article_text()

    article = get_test_article()

    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(get_test_article_elements(article), article_text, old_char_offset=0, new_char_offset=100)

    assert modified_text == article_text

    # DELETION
def test_article_element_modification_deletion():

    article_text = get_article_text()

    # test deletion of paragraph
    article = get_test_article()
    article_elements = get_test_article_elements(article)
    article_elements['pars'][0]._.delete()
    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article_elements, article_text, old_char_offset=0, new_char_offset=100)
    assert modified_text == article_text[:13] + article_text[194:]
    assert 0 == len(modified_article_elements['pars'])

    # test deletion of subparagraph
    article = get_test_article()
    article_elements = get_test_article_elements(article)
    article_elements['subpars'][0][0]._.delete()
    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article_elements, article_text, old_char_offset=0, new_char_offset=100)
    assert modified_text == article_text[:13] + article_text[194:]
    assert 0 == len(modified_article_elements['subpars'][0])

    # test deletion of point
    article = get_test_article()
    article_elements = get_test_article_elements(article)
    article_elements['points'][0][0][0]._.delete()
    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article_elements, article_text, old_char_offset=0, new_char_offset=100)
    assert modified_text == article_text[:122] + article_text[159:]
    assert 1 == len(modified_article_elements['points'][0][0])

def test_article_element_modification_replacement():

    article_text = get_article_text()

    # REPLACEMENT
    article = get_test_article()
    article_elements = get_test_article_elements(article)
    article_elements['pars'][0] = modify.replace_text(article_elements['pars'][0], 'This is a test.')
    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article_elements, article_text, old_char_offset=0, new_char_offset=100)
    assert modified_text == article_text[:13] + 'This is a test.' + article_text[194:]
    assert utils.get_element_text(modified_article_elements['pars'][0], replace_text=True) == 'This is a test.'
    assert len(modified_article_elements['pars']) == 1 and \
        len(modified_article_elements['subpars'][0]) == 1 and \
        len(modified_article_elements['points'][0][0]) == 0 and \
        len(modified_article_elements['indents'][0][0]) == 0


def test_article_element_modification_addition():

    article_text = get_article_text()

    # ADDITION
    article = get_test_article()
    article_elements = get_test_article_elements(article)

    # preapte article by adding article element sextension
    utils.set_extensions(article)

    article._.article_elements = [article_elements] # position of article 0

    # add a paragraph
    article._.add_article_element ('This is a test.', article=0, paragraph=0)

    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article._.article_elements[0], article_text, old_char_offset=0, new_char_offset=100)

    if modified_text.endswith('\n\n'):
        end_new_chars = '\n\n'
    else:
        end_new_chars = ''

    assert modified_text == article_text[:13] + '\n\nThis is a test.\n\n' + article_text[13:].strip() + end_new_chars





def test_modify_doc(eudoc, eu_wrapper, nlp):
    """Test general in and output of modify.modify_doc()."""

    eudoc_mod = modify.modify_doc(eudoc)

    assert type(eudoc_mod) == type(
        eudoc), 'modify_doc() did not return the same type of object as input.'

    assert type(eudoc_mod) == type(
        eudoc
    ), 'modify_doc() did not return the same type of object as input after running through eu_wrapper.'

    # try with nlp
    eudoc_mod = modify.modify_doc(eudoc, nlp=nlp, eu_wrapper=eu_wrapper)

    assert type(eudoc_mod) == type(
        eudoc
    ), 'modify_doc() did not return the same type of object as input when nlp was passed.'


def test_modify_doc_replacement(eudoc):
    """Test modify.modify_doc() for replacement of a random citation, recital, and article."""

    threshold = 0

    to_test = ['citations', 'recitals', 'articles']
    random_span_is = {}

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:
            random_span_is[span_type] = random.choice(
                range(len(eudoc.spans[span_type])))
            eudoc.spans[span_type][
                random_span_is[span_type]] = modify.replace_text(
                    eudoc.spans[span_type][random_span_is[span_type]],
                    'This is a test.')

    eudoc_mod = modify.modify_doc(eudoc)

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:

            assert eudoc_mod.spans[span_type][random_span_is[span_type]].text.strip(
            ) == 'This is a test.', 'modify_doc() did not replace the text of a random {}.'.format(
                span_type.title())


def test_modify_doc_deletion(eudoc, eu_wrapper):
    """Test modify.modify_doc() for deletion of a random citation, recital, and article."""

    threshold = 0

    to_test = ['citations', 'recitals', 'articles']

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:
            random_span_i = random.choice(range(len(eudoc.spans[span_type])))
            eudoc.spans[span_type][random_span_i] = modify.delete_text(
                eudoc.spans[span_type][random_span_i])

    eudoc_mod = modify.modify_doc(eudoc)

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:
            assert len(eudoc_mod.spans[span_type]) == len(
                eudoc.spans[span_type]) - 1, 'Deletion of {} failed.'.format(
                    span_type.title())


def test_modify_doc_addition(eudoc):
    """Test modify.modify_doc() for addition of a random citation, recital, and article."""

    to_test = ['citations', 'recitals', 'articles']
    random_span_is = {}

    for span_type in to_test:

        random_span_is[span_type] = [
            random.choice(range(len(eudoc.spans[span_type])))
            if len(eudoc.spans[span_type]) > 0 else 0
        ]

        eudoc._.add_element('This is a test.',
                            position=random_span_is[span_type][0],
                            element_type=span_type[:-1])

        # randomly add 1 more
        if random.random() > 0.5:

            eudoc._.add_element('This is a test.',
                                position='end',
                                element_type=span_type[:-1])

            random_span_is[span_type].append(len(eudoc.spans[span_type]) - 1)

    eudoc_mod = modify.modify_doc(eudoc)

    for span_type in to_test:

        for r_i in random_span_is[span_type]:
            assert eudoc_mod._.complexity[
                span_type] == eudoc._.complexity[span_type] + len(
                    random_span_is[span_type]
                ), 'modify_doc() did not add the correct number of {} to the count.'.format(
                    span_type.title())
            assert eudoc_mod.spans[span_type][r_i].text.strip(
            ) == 'This is a test.', 'modify_doc() did not add the text of a new {}.'.format(
                span_type.title())


def test_modify_doc_mix(eudoc):
    """Test modify.modify_doc() for a mix of modifications."""

    modification_operations = ['addition', 'deletion', 'replacement']
    parts = ['citations', 'recitals', 'articles']

    modifications = {
        op: {part: []
             for part in parts}
        for op in modification_operations
    }

    for modop in modification_operations:

        # randomly decide whether to do this operation
        if random.random() > 0.2:
            for part in parts:
                # randomly decide whether to modify this part
                if random.random() > 0.2:
                    if modop == 'addition':
                        modifications[modop][part] = [
                            random.choice(range(len(eudoc.spans[part])))
                            if len(eudoc.spans[part]) > 0 else 0
                        ]
                        eudoc._.add_element(
                            'This is a test.',
                            position=modifications[modop][part][0],
                            element_type=part[:-1])
                        # randomly add a couple more

                        while random.random() > 0.4:
                            eudoc._.add_element('This is a test.',
                                                position='end',
                                                element_type=part[:-1])
                            modifications[modop][part].append(
                                len(eudoc.spans[part]) - 1)

                    elif modop == 'deletion':

                        # make sure random deletion is not the in the added elements
                        t_r_i = 0
                        r = None
                        while True and len(eudoc.spans[part]) > 0:
                            r = random.choice(range(len(eudoc.spans[part])))
                            if r not in modifications['addition'][
                                    part] and r not in modifications[
                                        'deletion'][part]:
                                modifications[modop][part].append(r)
                                break
                            else:
                                r = None
                            t_r_i += 1
                            if t_r_i > 10:
                                break

                        if r is not None:
                            eudoc.spans[part][r] = modify.delete_text(
                                eudoc.spans[part][r])

                        # randomly delete 1 more
                        while random.random() > 0.4 and len(
                                eudoc.spans[part]) > len(
                                    modifications['addition'][part] +
                                    modifications['deletion'][part]):
                            # make sure random deletion is not the in the added elements
                            t_r_i = 0
                            r = None
                            while True:
                                r = random.choice(range(len(
                                    eudoc.spans[part])))
                                if r not in modifications['addition'][
                                        part] and r not in modifications[
                                            'deletion'][part]:
                                    modifications[modop][part].append(r)
                                    break
                                else:
                                    r = None
                                t_r_i += 1
                                if t_r_i > 10:
                                    break

                            if r is not None:
                                eudoc.spans[part][r] = modify.delete_text(
                                    eudoc.spans[part][r])

                    elif modop == 'replacement':
                        t_r_i = 0
                        r = None
                        while True and len(eudoc.spans[part]) > 0:
                            r = random.choice(range(len(eudoc.spans[part])))
                            if r not in modifications['addition'][
                                    part] and r not in modifications[
                                        'deletion'][
                                            part] and r not in modifications[
                                                'replacement'][part]:
                                modifications[modop][part].append(r)
                                break
                            else:
                                r = None
                            t_r_i += 1
                            if t_r_i > 10:
                                break

                        if r is not None:
                            eudoc.spans[part][r] = modify.replace_text(
                                eudoc.spans[part][r],
                                'This is a replaced test.')

                        # randomly replace 1 more
                        while random.random() > 0.4 and len(
                                eudoc.spans[part]) > len(
                                    modifications['addition'][part] +
                                    modifications['deletion'][part] +
                                    modifications['replacement'][part]):

                            t_r_i = 0
                            while True:
                                r = random.choice(range(len(
                                    eudoc.spans[part])))
                                if r not in modifications['addition'][
                                        part] and r not in modifications[
                                            'deletion'][
                                                part] and r not in modifications[
                                                    'replacement'][part]:
                                    modifications[modop][part].append(r)
                                    break
                                else:
                                    r = None
                                t_r_i += 1
                                if t_r_i > 10:
                                    break

                            if r is not None:
                                eudoc.spans[part][r] = modify.replace_text(
                                    eudoc.spans[part][r],
                                    'This is a replaced test.')

    eudoc_mod = modify.modify_doc(eudoc)

    # print the modifications
    print(modifications)

    # check
    for part in parts:
        # check that each part has the right number of elements
        assert eudoc_mod._.complexity[part] == eudoc._.complexity[part] + len(
            modifications['addition'][part]
        ) - len(
            modifications['deletion'][part]
        ), 'modify_doc() did not end up the correct number of {} after modification.'.format(
            part.title())

        # check that part has the right number of 'This is a test.' (additions) elements
        assert len([
            s for s in eudoc_mod.spans[part]
            if s.text.strip() == 'This is a test.'
        ]) == len(
            modifications['addition'][part]
        ), 'modify_doc() did not add the correct number of {} to the count.'.format(
            part.title())

        # check that part has the right number of 'This is a replaced test.' (replacements) elements
        assert len([
            s for s in eudoc_mod.spans[part]
            if s.text.strip() == 'This is a replaced test.'
        ]) == len(
            modifications['replacement'][part]
        ), 'modify_doc() did not replace the correct number of {} to the count.'.format(
            part.title())
