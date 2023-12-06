import spacy
import warnings
from spacy.tokens import Doc, Span, SpanGroup

from eucy.utils import set_extensions, determine_span_group_order, get_element_text, is_modified_span
from eucy.modify.article_elements import process_article_elements_modifications, any_modified_article_elements, recalculate_article_elements, adjust_article_element_offsets

from eucy.elements import article_elements_dict

def add_element(doc, new_text, element_type=None, position='end', article=None, paragraph = None, subparagraph = None, indent = None, point = None, add_ws=True):
    """Adds new text to a doc/span object and returns the object with the new text in the ._.add_text attribute

    Parameters
    ----------
    doc (Doc or Span):
        The doc object to be added to
    new_text (str):
        The new text to add
    element_type (str):
        The type of the new text. Must be one of 'citation', 'recital', 'article'. Other types are not supported yet. Default is None.
    position (str):
        The position to add the new text. Must be one of 'end', 'start' or an integer specifying the position. Default is 'end'.
    article (int):
        The article number of the new text (uses `_add_article_element` ignoring `element_type` and `position`). Default is None.
    paragraph (int, str):
        The paragraph number of the new text (uses `_add_article_element` ignoring `element_type` and `position`). Must be one of 'end', 'start' or an integer specifying the position. Default is None.
    subparagraph (int):
        The subparagraph number of the new text (uses `_add_article_element` ignoring `element_type` and `position`). Must be one of 'end', 'start' or an integer specifying the position. Default is None.
    indent (int):
        The indent number of the new text (uses `_add_article_element` ignoring `element_type` and `position`). Must be one of 'end', 'start' or an integer specifying the position. Default is None.

    add_ws (bool):
        Whether to add whitespace around the new text. Default is True.


    Returns
    -------
    doc (Doc or Span):
        The doc or span object with the added elements in the respective span group

    """

    # check if doc is a doc or span object
    assert isinstance(doc, (Doc)), "doc must be a Doc object"

    # make sure the doc has the extensions
    set_extensions(doc)

    if element_type and element_type in ['citation', 'recital', 'article']:

        doc._.add_element(new_text,
                          element_type=element_type,
                          position=position,
                          add_ws=add_ws)

    elif not element_type and any(['article', 'paragraph', 'subparagraph', 'indent', 'point']):

        doc._.add_article_element(new_text,
                       article=article,
                       paragraph=paragraph,
                          subparagraph=subparagraph,
                            indent=indent,
                            point=point,
                       add_ws=add_ws)

    else:
        raise ValueError("element_type must be one of 'citation', 'recital', 'article' or None. If None, article, paragraph, subparagraph, indent, or point must be specified.")

    return doc


def replace_text(doc, new_text, keep_ws=True, deletion_threshold=None):
    """Adds replacement text for a span/doc object and returns the object with the new in the ._.replacement_text attribute

    Parameters
    ----------
    doc (Doc or Span):
        The doc or span object to be replaced
    new_text (str):
        The new text to replace the current text
    deletion_threshold (int):
        If the new text is shorter than the deletion threshold (excluding whitespace), the doc/span will be marked as deleted. If None (default), it will never be marked as deleted.


    Returns
    -------
    doc (Doc or Span):
        The doc or span object with the new text in the ._.replacement_text attribute

    """

    # check if doc is a doc or span object
    assert isinstance(doc, (Span, Doc)), "doc must be a Doc or Span object"

    # make sure the doc has the extensions
    set_extensions(doc)

    doc._.replace_text(new_text,
                       keep_ws=keep_ws,
                       deletion_threshold=deletion_threshold)

    return doc


def delete_text(doc, warn_empty_group=True):
    """Marks a doc/span object as deleted

    Parameters
    ----------
    doc (Doc or Span):
        The doc or span object to be deleted

    Returns
    -------
    doc (Doc or Span):
        The doc or span object marked as deleted

    """

    # check if doc is a doc or span object
    assert isinstance(doc, (Doc, Span)), "doc must be a Doc or Span object"

    # make sure the doc has the extensions
    set_extensions(doc)

    doc._.delete_text(warn_empty_group=warn_empty_group)

    return doc


def modify_doc(doc,
               nlp=None,
               eu_wrapper=None,
               add_spans=True,
               return_doc=True,
               delete_spans=True):
    """Modify the original text in the doc to contain the new replacement text (`._.replacement_text`) where applicable.

    Parameters
    ----------
        doc (spacy.tokens.Doc): spaCy doc
        nlp (spacy.lang): spaCy model to use for new doc. If None, `spacy.blank("en")` is used.
        add_spans (bool): If True, add all element non-overlapping attributes/spans from the original doc to the new doc. If False, only the text is modified.
        return_doc (bool): If True, return the new doc. If False, return the new text.
        delete_spans (bool): If True, delete all elements spans shorter than 5 characters (excluding whitespace) or marked as deleted (`._.deleted`) from the new doc.

    Returns:
        spacy.tokens.Doc: spaCy doc with modified text and all element attributes/spans from the original doc

    """

    assert isinstance(doc, Doc), 'doc must be a spaCy Doc'

    if not nlp:
        nlp = spacy.blank("en")

    new_text = ''
    old_text = doc.text

    def new_doc_span(span, new_doc):
        new_span = new_doc.char_span(span._.new_start_char,
                                     span._.new_end_char,
                                     alignment_mode='expand',
                                     label=span.label_)

        # copy extension attributes
        for attr in dir(span._):
            if span.has_extension(attr):
                if new_span.has_extension(attr):
                    new_span._.set(attr, span._.get(attr))

        return new_span

    # set Span extensions
    Span.set_extension("new_start_char", default=None, force=True)
    Span.set_extension("new_end_char", default=None, force=True)
    Span.set_extension("replacement_span", method=new_doc_span, force=True)
    if not Span.has_extension('added'):
        Span.set_extension("added", default=False)

    # get all non-overlapping spangroups
    non_overlap_span_groups = determine_span_group_order(doc)

    old_spans = {}

    for group in non_overlap_span_groups:
        old_spans[group] = doc.spans[group].copy()

    old_text_char_i = 0

    sg_without_new_elements = lambda x: [
        s for s in doc.spans[x] if not s._.new_element
    ]

    # sort old_spans keys by start char of first span
    old_spans = {
        ke: va
        for ke, va in sorted(
            old_spans.items(),
            key=lambda item: min(
                [s.start_char for s in item[1]
                 if not s._.new_element] if len(sg_without_new_elements(item[0]))>0 else [s._.char_pos for s in item[1]] + [len(doc.text)]))
    }  # sort by start char of first span
       # if not a new element (add len of doc so that there's no exception in case of empty group)
       # if there's only new elements, use that instead


    # old_new_article_elements = []

    # create new text
    for k, spangroup in old_spans.items():

        element_i = 0 # keep track of existing elements (used for article elements)

        for span_i, span in enumerate(spangroup):

            # Deletion
            if (span.has_extension('deleted') and span._.deleted) or (
                    span.has_extension('deleted')
                    and span._.replacement_text is not None
                    and len(span._.replacement_text.strip()) < 5):

                # if we're deleting the first span, we need to add the text before it
                if old_text_char_i == 0 and span.start_char > 0:
                    new_text += old_text[old_text_char_i:span.start_char]

                # check for replacement text (keep_ws = True in delete())
                if span.has_extension(
                        'replacement_text'
                ) and span._.replacement_text is not None:
                    new_text += span._.replacement_text

                # mark span as added
                span._.added = True

                # move old text char index
                old_text_char_i = span.end_char

                if not span._.deleted:
                    span._.deleted = True


                element_i += 1

                continue

            # Addition
            elif span.has_extension('new_element') and span._.new_element:

                # add a new element

                # add any text before the new element
                new_text += old_text[old_text_char_i:span._.char_pos]

                # move old text char index
                old_text_char_i = span._.char_pos

                # if we're dealing with citations/recitals there may be no-existing elements
                #  so we need to check for that and add the text introducing the elements
                if span_i == 0 and k in ['citations', 'recitals'] and len([s for s in doc.spans[k] if not s._.new_element]) == 0:
                    if k == 'recitals' and not get_element_text(span, replace_text=True).lower().strip().startswith('whereas'):
                        new_text += 'Whereas:\n\n'

                span._.new_start_char = len(new_text)

                # if k == 'articles':
                #     # create article elements for new article
                #     old_new_article_elements.append(recalculate_article_elements(get_element_text(span, replace_text=True), article_offset=len(new_text)))

                # check for replacement text (keep_ws = True in delete())
                if span.has_extension(
                        'replacement_text'
                ) and span._.replacement_text is not None:
                    new_text += span._.replacement_text

                span._.new_end_char = len(new_text)

                continue

            # Replacement
            new_text += old_text[old_text_char_i:span.start_char]
            # set new text char index
            span._.new_start_char = len(new_text)

            if k == 'articles':
                ## if we're dealing with articles, we also need to check article elements for paragraph-level changes
                ## ideally, an article would either have replacement text or changed article elements, but not both
                new_article_elements = None

                if k == 'articles' and doc.has_extension('article_elements') and any_modified_article_elements(doc._.article_elements[element_i]):

                    if is_modified_span(span):
                        warnings.warn("Article {} is modified and has modified article elements. This is not supported. The replacement for the article elements will be used.".format(span._.element_numstr))

                    replacement_text, new_article_elements = process_article_elements_modifications(doc._.article_elements[element_i], article_text = span.text_with_ws, new_char_offset = len(new_text), old_char_offset = span.start_char)
                else:
                    # Replacement
                    # get replacement text
                    replacement_text = span._.replacement_text if span.has_extension(
                        'replacement_text'
                    ) and span._.replacement_text is not None else span.text_with_ws
                # if new_article_elements is not None:
                #     # adjust article elements spans (if replaced and if no mod)
                #     if is_modified_span(span):
                #         new_article_elements = recalculate_article_elements(get_element_text(span, replace_text=True), article_offset=len(new_text))
                #     else:
                #         new_article_elements = adjust_article_element_offsets(doc._.article_elements[element_i], old_offset=span.start_char, new_offset=len(new_text))

                # old_new_article_elements.append(new_article_elements)
            else:
                # Replacement
                # get replacement text
                replacement_text = span._.replacement_text if span.has_extension(
                    'replacement_text'
                ) and span._.replacement_text is not None else span.text_with_ws

            # add replacement text to new text
            new_text += replacement_text

            span._.new_end_char = len(new_text)

            # update old text char index
            old_text_char_i = span.end_char

            element_i += 1


    # add remaining text
    new_text += old_text[old_text_char_i:]

    if not return_doc:
        return new_text

    # create new doc
    new_doc = nlp(new_text)

    if not add_spans:
        return new_doc

    # add new spans to new doc
    for sk, sg in old_spans.items():

        # add span group
        new_doc.spans[sk] = SpanGroup(new_doc, name=sk, attrs=sg.attrs)

        for s_i, old_new_span in enumerate(sg):
            if old_new_span._.deleted:
                continue

            if old_new_span._.added:
                old_new_span._.new_element = False

            if old_new_span.has_extension('new_start_char'):
                new_doc.spans[sk].append(
                    old_new_span._.replacement_span(new_doc))

    # make sure all spangroups are present
    for sk in doc.spans.keys():
        if sk not in new_doc.spans.keys():
            new_doc.spans[sk] = SpanGroup(new_doc, name=sk)

    # recover article elements
    #  using new_old_article_elements
    new_doc._.article_elements = []
    for article in new_doc.spans['articles']:
        new_doc._.article_elements.append(article_elements_dict(article))


    # recover _.parts
    if not doc.has_extension('parts'):
        Doc.set_extension('parts', default=None, force=True)

    part_names = ['citations', 'recitals', 'enacting', 'enacting_w_toc']

    new_parts = {}

    ## for each part in the old doc, get the distances between the part start/end and the first/last element
    for part_name in part_names:
        # part = [s for s in doc._.parts.get(part_name) if s._.new_start_char is not None and s._.new_end_char is not None]
        #
        # if part is None:
        #     new_parts[part_name] = None
        #     continue

        if part_name == 'citations':
            element_name = 'citations'
        elif part_name == 'recitals':
            element_name = 'recitals'
        elif part_name == 'enacting':
            element_name = 'articles'
        elif part_name == 'enacting_w_toc':
            element_name = 'articles'

        # check for case where all elements are deleted/there are no elements
        if len(new_doc.spans[element_name]) == 0:
            new_parts[part_name] = None
            continue

        # get first element start and last element end of the new doc
        first_element_start_char = new_doc.spans[element_name][0].start_char
        last_element_end_char = new_doc.spans[element_name][-1].end_char

        # get new part
        new_part = new_doc.char_span(first_element_start_char,
                                     last_element_end_char,
                                     alignment_mode='expand')

        # add new part to new doc
        new_parts[part_name] = new_part

    # handle 'annex' part

    if doc._.parts['annex'] is None:
        new_parts['annex'] = None
    else:
        ## get distance between enacting and annex
        annex_dist = doc._.parts['enacting'].end_char - doc._.parts['annex'].start_char

        ## get new annex start and end
        new_annex_start_char = new_parts['enacting'].end_char + annex_dist
        new_annex_end_char = new_annex_start_char + len(
            doc._.parts['annex'].text)

        ## get new annex
        new_annex = new_doc.char_span(new_annex_start_char,
                                      new_annex_end_char,
                                      alignment_mode='expand')
        new_parts['annex'] = new_annex

    # add new parts to new doc
    new_doc._.parts = new_parts

    # re-run eu-wrapper to get complexity and other metadata
    if not eu_wrapper:
        from eucy.eucy import EuWrapper
        eu_wrapper = EuWrapper(nlp)

    new_doc = eu_wrapper(new_doc)

    return new_doc
