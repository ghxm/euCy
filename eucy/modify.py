from spacy.tokens import Span, Doc, SpanGroup
import spacy
from eucy import utils



def replace_text(doc, new_text, keep_ws = True, deletion_threshold = None):

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
    assert isinstance(doc, (Span)), "doc must be a Doc or Span object"

    # check if new text is a string
    assert isinstance(new_text, str), "New text must be a string"

    # make sure the doc has the extensions
    utils.set_extensions(doc)

    doc._.replace_text(new_text, keep_ws = keep_ws, deletion_threshold = deletion_threshold)

    return doc



def delete_text(doc):
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

    # check if deleted attribute exists
    if not doc.has_extension('deleted'):
        if isinstance(doc, Doc):
            Doc.set_extension('deleted', default=False, force=False)
        elif isinstance(doc, Span):
            Span.set_extension('deleted', default=False, force=False)

    doc._.deleted = True

    return doc


def modify_doc(doc, nlp = None, add_spans = True, return_doc = True, delete_spans = True):
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

    if nlp is None:
        # load blank model
        nlp = spacy.blank("en")

    new_text = ''
    old_text = doc.text

    def new_doc_span(span, new_doc):
        new_span = new_doc.char_span(span._.new_start_char, span._.new_end_char, alignment_mode='expand', label=span.label_)

        # copy extension attributes
        for attr in dir(span._):
            if span.has_extension(attr):
                if new_span.has_extension(attr):
                    new_span._.set(attr, span._.get(attr))

        return new_span

    # set Span extensions
    Span.set_extension("new_start_char", default = None, force=True)
    Span.set_extension("new_end_char", default = None, force=True)
    Span.set_extension("replacement_span", method = new_doc_span, force=True)

    # get all non-overlapping spangroups
    non_overlap_span_groups = ['citations', 'recitals', 'articles']

    old_spans = {}

    for group in non_overlap_span_groups:
        old_spans[group] = doc.spans[group].copy()

    old_text_char_i = 0


    # create new text
    for k, spangroup in old_spans.items():

        for span_i, span in enumerate(spangroup):

            # if the element got deleted, pop it from the spangroup
            if (span.has_extension('deleted') and span._.deleted) or (span.has_extension('deleted') and span._.replacement_text is not None and len(span._.replacement_text.strip()) < 5):

                # if we're deleting the first span, we need to add the text before it
                if old_text_char_i == 0 and span.start_char > 0:
                    new_text += old_text[old_text_char_i:span.start_char]

                # move old text char index
                old_text_char_i = span.end_char

                if not span._.deleted:
                    span._.deleted = True
                continue

            # get replacement text
            replacement_text = span._.replacement_text if span.has_extension('replacement_text') and span._.replacement_text is not None else span.text_with_ws

            new_text += old_text[old_text_char_i:span.start_char]

            # set new text char index
            span._.new_start_char = len(new_text)
            span._.new_end_char = span._.new_start_char + len(replacement_text)

            # add replacement text to new text
            new_text += replacement_text

            # update old text char index
            old_text_char_i = span.end_char


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
            if old_new_span.has_extension('new_start_char'):
                new_doc.spans[sk].append(old_new_span._.replacement_span(new_doc))


    # recover _.parts

    if not doc.has_extension('parts'):
        Doc.set_extension('parts', default = None, force=True)


    part_names = ['citations', 'recitals', 'enacting', 'enacting_w_toc']

    new_parts = {}

    ## for each part in the old doc, get the distances between the part start/end and the first/last element
    for part_name in part_names:
        part = doc._.parts.get(part_name)

        if part is None:
            new_parts[part_name] = None
            continue

        if part_name == 'citations':
            element_name = 'citations'
        elif part_name == 'recitals':
            element_name = 'recitals'
        elif part_name == 'enacting':
            element_name = 'articles'
        elif part_name == 'enacting_w_toc':
            element_name = 'articles'

        # get part start and end
        part_start_char = doc._.parts[part_name].start_char
        part_end_char = doc._.parts[part_name].end_char

        # @TODO handle cases where all elements are deleted

        # get first element start and last element end
        first_element_start_char = doc.spans[element_name][0].start_char
        last_element_end_char = doc.spans[element_name][-1].end_char

        # get distances
        first_element_dist = first_element_start_char - part_start_char
        last_element_dist = part_end_char - last_element_end_char

        # get new part start and end
        new_part_start_char = new_doc.spans[element_name][0].start_char - first_element_dist
        new_part_end_char = new_doc.spans[element_name][-1].end_char + last_element_dist

        # get new part
        new_part = new_doc.char_span(new_part_start_char, new_part_end_char, alignment_mode='expand')

        # add new part to new doc
        new_parts[part_name] = new_part

    # handle 'annex' part

    if doc._.parts['annex'] is None:
        new_parts['annex'] = None
    else:
        ## distance between enacting end and annex start
        enacting_end_char = doc._.parts['enacting'].end_char
        annex_start_char = doc._.parts['annex'].start_char
        annex_dist = annex_start_char - enacting_end_char

        ## get new annex start and end
        new_annex_start_char = new_parts['enacting'].end_char + annex_dist
        new_annex_end_char = new_annex_start_char + len(doc._.parts['annex'].text)

        ## get new annex
        new_annex = new_doc.char_span(new_annex_start_char, new_annex_end_char, alignment_mode='expand')
        new_parts['annex'] = new_annex

    # add new parts to new doc
    new_doc._.parts = new_parts

    # @TODO possible to recover article_elements? -> otherwise elements might no be detected by e.g. elemount count as in current setup -> adjust eucywrapper to work with preconfiugred spans
    # @TODO re-run eu-wrapper to get complexity and other metadata

    return new_doc

