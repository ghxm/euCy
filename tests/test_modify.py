import pytest
from eucy import modify
import random


def _test_modify_doc(eudoc, eu_wrapper, nlp):
    """Test general in and output of modify.modify_doc()."""

    eudoc_mod = modify.modify_doc(eudoc)

    assert type(eudoc_mod) == type(eudoc), 'modify_doc() did not return the same type of object as input.'

    assert type(eudoc_mod) == type(eudoc), 'modify_doc() did not return the same type of object as input after running through eu_wrapper.'

    # try with nlp
    eudoc_mod = modify.modify_doc(eudoc, nlp=nlp, eu_wrapper=eu_wrapper)

    assert type(eudoc_mod) == type(eudoc), 'modify_doc() did not return the same type of object as input when nlp was passed.'



def _test_modify_doc_replacement(eudoc):
    """Test modify.modify_doc() for replacement of a random citation, recital, and article."""

    threshold = 0

    to_test = ['citations', 'recitals', 'articles']
    random_span_is = {}

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:
            random_span_is[span_type] = random.choice(range(len(eudoc.spans[span_type])))
            eudoc.spans[span_type][random_span_is[span_type]] = modify.replace_text(eudoc.spans[span_type][random_span_is[span_type]], 'This is a test.')

    eudoc_mod = modify.modify_doc(eudoc)

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:

            assert eudoc_mod.spans[span_type][random_span_is[span_type]].text == 'This is a test.', 'modify_doc() did not replace the text of a random {}.'.format(span_type.title())


def _test_modify_doc_deletion(eudoc, eu_wrapper):
    """Test modify.modify_doc() for deletion of a random citation, recital, and article."""

    threshold = 0

    to_test = ['citations', 'recitals', 'articles']

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:
            random_span_i = random.choice(range(len(eudoc.spans[span_type])))
            eudoc.spans[span_type][random_span_i] = modify.delete_text(eudoc.spans[span_type][random_span_i])

    eudoc_mod = modify.modify_doc(eudoc)

    for span_type in to_test:
        if len(eudoc.spans[span_type]) > threshold:
            assert len(eudoc_mod.spans[span_type]) == len(eudoc.spans[span_type]) - 1, 'Deletion of {} failed.'.format(span_type.title())

def _test_modify_doc_addition(eudoc):
    """Test modify.modify_doc() for addition of a random citation, recital, and article."""

    to_test = ['citations', 'recitals', 'articles']
    random_span_is = {}

    for span_type in to_test:

        random_span_is[span_type] = [random.choice(range(len(eudoc.spans[span_type]))) if len(eudoc.spans[span_type]) > 0 else 0]

        eudoc._.add_element('This is a test.', position=random_span_is[span_type][0], element_type=span_type[:-1])


        # randomly add 1 more
        if random.random() > 0.5:

            eudoc._.add_element('This is a test.', position='end', element_type=span_type[:-1])

            random_span_is[span_type].append(len(eudoc.spans[span_type])-1)


    eudoc_mod = modify.modify_doc(eudoc)

    for span_type in to_test:

        for r_i in random_span_is[span_type]:
            assert eudoc_mod._.complexity[span_type] == eudoc._.complexity[span_type] + len(random_span_is[span_type]), 'modify_doc() did not add the correct number of {} to the count.'.format(span_type.title())
            assert eudoc_mod.spans[span_type][r_i].text.strip() == 'This is a test.', 'modify_doc() did not add the text of a new {}.'.format(span_type.title())




def test_modify_doc_mix(eudoc):
    """Test modify.modify_doc() for a mix of modifications."""

    modification_operations = ['addition', 'deletion', 'replacement']
    parts = ['citations', 'recitals', 'articles']

    modifications = {op: {part: [] for part in parts} for op in modification_operations}

    for modop in modification_operations:

        # randomly decide whether to do this operation
        if random.random() > 0.2:
            for part in parts:
                # randomly decide whether to modify this part
                if random.random() > 0.2:
                    if modop == 'addition':
                        modifications[modop][part] = [random.choice(range(len(eudoc.spans[part]))) if len(eudoc.spans[part]) > 0 else 0]
                        eudoc._.add_element('This is a test.', position=modifications[modop][part][0], element_type=part[:-1])
                        # randomly add a couple more

                        while random.random() > 0.4:
                            eudoc._.add_element('This is a test.', position='end', element_type=part[:-1])
                            modifications[modop][part].append(len(eudoc.spans[part])-1)


                    elif modop == 'deletion':

                        # make sure random deletion is not the in the added elements
                        t_r_i = 0
                        r = None
                        while True and len(eudoc.spans[part]) > 0:
                            r = random.choice(range(len(eudoc.spans[part])))
                            if r not in modifications['addition'][part] and r not in modifications['deletion'][part]:
                                modifications[modop][part].append(r)
                                break
                            else:
                                r = None
                            t_r_i += 1
                            if t_r_i > 10:
                                break

                        if r is not None:
                            eudoc.spans[part][r] = modify.delete_text(eudoc.spans[part][r])


                        # randomly delete 1 more
                        while random.random() > 0.4 and len(eudoc.spans[part]) > len(modifications['addition'][part] + modifications['deletion'][part]):
                            # make sure random deletion is not the in the added elements
                            t_r_i = 0
                            r = None
                            while True:
                                r = random.choice(range(len(eudoc.spans[part])))
                                if r not in modifications['addition'][part] and r not in modifications['deletion'][part]:
                                    modifications[modop][part].append(r)
                                    break
                                else:
                                    r = None
                                t_r_i += 1
                                if t_r_i > 10:
                                    break

                            if r is not None:
                                eudoc.spans[part][r] = modify.delete_text(eudoc.spans[part][r])

                    elif modop == 'replacement':
                        t_r_i = 0
                        r = None
                        while True and len(eudoc.spans[part]) > 0:
                            r = random.choice(range(len(eudoc.spans[part])))
                            if r not in modifications['addition'][part] and r not in modifications['deletion'][part] and r not in modifications['replacement'][part]:
                                modifications[modop][part].append(r)
                                break
                            else:
                                r = None
                            t_r_i += 1
                            if t_r_i > 10:
                                break

                        if r is not None:
                            eudoc.spans[part][r] = modify.replace_text(eudoc.spans[part][r], 'This is a replaced test.')

                        # randomly replace 1 more
                        while random.random() > 0.4 and len(eudoc.spans[part]) > len(modifications['addition'][part] + modifications['deletion'][part] + modifications['replacement'][part]):

                            t_r_i = 0
                            while True:
                                r = random.choice(range(len(eudoc.spans[part])))
                                if r not in modifications['addition'][part] and r not in modifications['deletion'][part] and r not in modifications['replacement'][part]:
                                    modifications[modop][part].append(r)
                                    break
                                else:
                                    r = None
                                t_r_i += 1
                                if t_r_i > 10:
                                    break

                            if r is not None:
                                eudoc.spans[part][r] = modify.replace_text(eudoc.spans[part][r], 'This is a replaced test.')

    eudoc_mod = modify.modify_doc(eudoc)

    # print the modifications
    print(modifications)

    # check
    for part in parts:
        # check that each part has the right number of elements
        assert eudoc_mod._.complexity[part] == eudoc._.complexity[part] + len(modifications['addition'][part]) - len(modifications['deletion'][part]), 'modify_doc() did not end up the correct number of {} after modification.'.format(part.title())

        # check that part has the right number of 'This is a test.' (additions) elements
        assert len([s for s in eudoc_mod.spans[part] if s.text.strip() == 'This is a test.']) == len(modifications['addition'][part]), 'modify_doc() did not add the correct number of {} to the count.'.format(part.title())

        # check that part has the right number of 'This is a replaced test.' (replacements) elements
        assert len([s for s in eudoc_mod.spans[part] if s.text.strip() == 'This is a replaced test.']) == len(modifications['replacement'][part]), 'modify_doc() did not replace the correct number of {} to the count.'.format(part.title())








