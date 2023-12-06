#!/usr/bin/env python
"""Tests for `euCy` package to ensure modification of documents and elements works."""
# pylint: disable=redefined-outer-name

import random
import re

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

    # add article element extensions
    for span in modify.article_elements.get_article_element_spans(article_elements):
        utils.set_extensions(span)

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

    # prepare article by adding article elements extensions
    utils.set_extensions(article)

    article._.article_elements = [article_elements] # position of article 0

    # add a paragraph
    article._.add_article_element ('This is a test.', article=0, paragraph=0)
    # add a point
    article._.add_article_element ('aa) This is a test.', article=0, paragraph=0, subparagraph=0, point=1)

    modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article._.article_elements[0], article_text, old_char_offset=0, new_char_offset=100)

    if modified_text.endswith('\n\n'):
        end_new_chars = '\n\n'
    elif modified_text.endswith('\n'):
        end_new_chars = '\n'
    else:
        end_new_chars = ''

    assert modified_text == article_text[:13] + '\n\nThis is a test.\n\n' + article_text[13:159] + '\n\naa) This is a test.\n\n' + article_text[159:-2] + end_new_chars

def test_article_element_modification_mix():

        article_text = get_article_text()

        # MIX
        article = get_test_article()
        article_elements = get_test_article_elements(article)

        # prepare article by adding article elements extensions
        utils.set_extensions(article)
        article._.article_elements = [article_elements] # position of article 0

        # add a paragraph
        article._.add_article_element ('This is a test.', article=0, paragraph=0)
        # add another paragraph
        article._.add_article_element ('This is a test paragraph.', article=0, paragraph='end')
        # add another one
        article._.add_article_element ('This is a test, too.', article=0, paragraph='end')

        # replace a point
        modify.replace_text(article._.article_elements[0]['points'][0][0][0], 'a) This is a replaced test.')
        # add a point
        article._.add_article_element ('c) This is a test.', article=0, paragraph=0, subparagraph=0, point='end')
        # delete a point
        article._.article_elements[0]['points'][0][0][1]._.delete()


        modified_text, modified_article_elements = modify.article_elements.process_article_elements_modifications(article._.article_elements[0], article_text, old_char_offset=0, new_char_offset=100)

        if modified_text.endswith('\n\n'):
            end_new_chars = '\n\n'
        elif modified_text.endswith('\n'):
            end_new_chars = '\n'
        else:
            end_new_chars = ''

        assert (modified_text == article_text[:13] +
                '\n\nThis is a test.\n\n' + article_text[13:122] +
                'a) This is a replaced test.\n\n\n\n' + # article_text[159:] +
                'c) This is a test.\n\n\n\n' +
                'This is a test paragraph.\n\n\n\n' +
                'This is a test, too.' +
                end_new_chars)


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

            print(random_span_is[span_type])

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

    def get_modified_index(original_index, part):

        modified_index = original_index
        for operation in ['addition']:
            for index in modifications[operation][part]:
                if index <= original_index:
                    if operation == 'addition':
                        modified_index += 1
        return modified_index

    modification_operations = ['addition', 'deletion', 'replacement']
    parts = ['citations', 'recitals', 'articles']


    original_part_n = {part: len(eudoc.spans[part]) for part in parts}

    modifications = {
        op: {part: []
             for part in parts}
        for op in modification_operations
    }

    modifications_paragraphs = {
        op: {article_i: []
            for article_i in range(len(eudoc._.article_elements))}
        for op in modification_operations
    }

    deleted_paragraph_strings = []

    for modop in modification_operations:

        # randomly decide whether to do this operation
        if random.random() > 0.2:
            for part in parts:
                # randomly decide whether to modify this part
                if random.random() > 0.2:
                    if modop == 'addition':

                        r = random.choice(range(original_part_n[part])) if original_part_n[part] > 0 else 0

                        r = get_modified_index(r, part)

                        modifications[modop][part] = [
                            r
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
                        while True and original_part_n[part] > 0:
                            r = random.choice(range(original_part_n[part])) if original_part_n[part] > 0 else None

                            if r is None:
                                break

                            r = get_modified_index(r, part)

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
                                r = random.choice(range(original_part_n[part]))

                                r = get_modified_index(r, part)

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
                        while True and original_part_n[part] > 0:
                            r = random.choice(range(original_part_n[part]))
                            r = get_modified_index(r, part)

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
                        while random.random() > 0.4 and original_part_n[part] > len(
                                    modifications['addition'][part] +
                                    modifications['deletion'][part] +
                                    modifications['replacement'][part]):

                            t_r_i = 0
                            while True:
                                r = random.choice(range(original_part_n[part]))
                                r = get_modified_index(r, part)

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
    for modop in modification_operations:
        # paragraphs
        for article_i in modifications_paragraphs[modop].keys():
            if get_modified_index(article_i, 'articles') in modifications['deletion']['articles'] or get_modified_index(
                article_i, 'articles') in modifications['replacement']['articles'] or get_modified_index(article_i,
                                                                                                         'articles') in \
                modifications['addition']['articles']:
                # skip if article was deleted, replaced or added
                continue
            # make sure articles were not deleted or replaced already
            if random.random() > 0.2:
                if modop == 'addition':
                    # add a paragraph to the end of the article
                    eudoc._.add_article_element(
                        'This is an article element addition test.',
                        article=article_i,
                        paragraph='end'
                    )

                    modifications_paragraphs[modop][article_i].append(len(eudoc._.article_elements[article_i]['pars'])-1)

                    # randomly add a couple more
                    while random.random() > 0.6:
                        eudoc._.add_article_element('This is an article element addition test.',
                                                    article=article_i,
                                                    paragraph='end')
                        modifications_paragraphs[modop][article_i].append(
                            len(eudoc._.article_elements[article_i]['pars']) - 1)

                elif modop == 'replacement':

                    if len(modifications_paragraphs['deletion'][article_i]) >= len(eudoc._.article_elements[article_i]['pars']):
                        # skip if all paragraphs were deleted
                        continue

                    r_par = None

                    max_tries = 5
                    tries = 0

                    while r_par is None or (r_par._.new_element or r_par._.deleted or r_par._.replacement_text):

                        if tries > max_tries:
                            r_par = None
                            break

                        tries += 1

                        # choose a random paragraph in the article
                        r = random.choice(range(len(eudoc._.article_elements[article_i]['pars'])))
                        r_par = eudoc._.article_elements[article_i]['pars'][r]

                    if r_par is None:
                        continue

                    r_par._.replace_text('This is an article element replacement test.')

                    modifications_paragraphs[modop][article_i].append(r)

                elif modop == 'deletion':

                    if len(modifications_paragraphs['deletion'][article_i]) >= len(
                        eudoc._.article_elements[article_i]['pars']):
                        # skip if all paragraphs were deleted
                        continue

                    r_par = None

                    max_tries = 5
                    tries = 0

                    while r_par is None or (r_par._.new_element or r_par._.deleted or r_par._.replacement_text):

                        if tries > max_tries:
                            r_par = None
                            break

                        tries += 1

                        # choose a random paragraph in the article
                        r = random.choice(range(len(eudoc._.article_elements[article_i]['pars'])))
                        r_par = eudoc._.article_elements[article_i]['pars'][r]

                    if r_par is None:
                        continue

                    r_par._.delete()
                    deleted_paragraph_strings.append(r_par.text)

                    modifications_paragraphs[modop][article_i].append(r)

    eudoc_mod = modify.modify_doc(eudoc)

    # print the modifications
    print('\n')
    print(modifications)
    print(modifications_paragraphs)

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
        ), 'modify_doc() did not replace the correct number of {}.'.format(
            part.title())

    # check article element modifications

    # TODO (after implementation of article element recovery) check that each article has the right number of elements

    # check that the overall doc has the right number of 'This is an article element addition test.' (additions) elements
    # TODO check on article basis
    assert sum([
        s.text.count('This is an article element addition test.') for s in eudoc_mod.spans['articles']
    ]) == len(
        utils.flatten([v for k, v in modifications_paragraphs['addition'].items()])
    ), 'modify_doc() did not add the correct number of paragraphs to the count.'

    # check that the overall doc has the right number of 'This is an article element replacement test.' (replacements) elements
    # TODO check on article basis
    for article_i in range(len(eudoc._.article_elements)):
        assert sum([
            s.text.count('This is an article element replacement test.') for s in eudoc_mod.spans['articles']
        ]) == len(
            utils.flatten([v for k, v in modifications_paragraphs['replacement'].items()])
        ), 'modify_doc() did not replace the correct number of paragraphs.'

    if sum([
        0 if eudoc_mod._.parts['enacting'] is None else eudoc_mod._.parts['enacting'].text.count(s.strip())
        for s in deleted_paragraph_strings
    ]) > 0:
        print('Deleted paragraphs:')
        for s in deleted_paragraph_strings:
            print(s)

    # check that the overall doc does not contain the deleted paragraphs
    # TODO check on article basis
    assert sum([
        0 if eudoc_mod._.parts['enacting'] is None else eudoc_mod._.parts['enacting'].text.count(s.strip())
        for s in deleted_paragraph_strings
    ]) == 0, 'modify_doc() did not delete the correct number of paragraphs.'
