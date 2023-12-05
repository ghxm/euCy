from eucy.utils import is_modified_span, get_element_text, set_extensions, flatten
from eucy.elements import paragraphs, subparagraphs, points, indents
from spacy.tokens import Span, Doc
from spacy import blank



def get_article_element_spans(article_elements):
    """
    Get all spans from the article elements.
    """

    spans = []

    spans.extend(flatten(article_elements['pars']))
    spans.extend(flatten(article_elements['subpars']))
    spans.extend(flatten(article_elements['points']))
    spans.extend(flatten(article_elements['indents']))

    return spans


def adjust_article_element_offsets(article_elements, old_offset, new_offset):

    spans = get_article_element_spans(article_elements)

    for span in spans:
        span._.new_start_char = span.start_char + new_offset - old_offset
        span._.new_end_char = span.end_char + new_offset - old_offset

    return article_elements

def any_modified_article_elements(article_elements):
    """
    Check if there are any modified article elements in the list of article elements.
    """

    spans = get_article_element_spans(article_elements)

    return any([is_modified_span(span) for span in spans])

def get_modified_article_elements(article_elements):

    """
    Get all modified article elements in the list of article elements.
    """

    spans = get_article_element_spans(article_elements)

    return [span for span in spans if is_modified_span(span)]


def recalculate_article_elements (article, article_offset = 0):

        """
        Get the article elements for a given article text and return them as a dictionary.

        Parameters
        ----------
        article : str or Span or Doc
            The article text or span or doc.
        article_offset : int, optional
            The article offset in the document, by default 0.

        Returns
        -------
        dict
            The article elements as a dictionary.
        """

        article_doc = None

        if isinstance(article, str):
            article_text = article
        elif isinstance(article, Span):
            article_text = article.text
        elif isinstance(article, Doc):
            article_text = article.text
            article_doc = article
        else:
            raise TypeError("par must be str, Span or Doc")

        if not article_doc:
            article_doc = blank("en")(article_text)

        # identify paragraphs
        pars = paragraphs(article_doc)

        # adjust paragraph offsets
        if not Span.has_extension('new_start_char'):
            Span.set_extension("new_start_char", default=None, force=True)
        if not Span.has_extension('new_end_char'):
            Span.set_extension("new_end_char", default=None, force=True)

        article_es = {
            'pars': [],
            'subpars': [],
            'points': [],
            'indents': []
        }

        for par in pars:
            par._.new_start_char = par.start_char + article_offset
            par._.new_end_char = par.end_char + article_offset
            article_es['pars'].append(par)

            # paragraph subelements
            par_es = recalculate_paragraph_subelements(par, par_offset = par._.new_start_char)

            article_es['subpars'].append(par_es['subpars'])
            article_es['points'].append(par_es['points'])
            article_es['indents'].append(par_es['indents'])

        # if there are no pars, add blank article element lists
        if len(article_es['pars']) == 0:
            article_es['subpars'] = [[]]
            article_es['points'] = [[[]]]
            article_es['indents'] = [[[[]]]]

        return article_es


def recalculate_paragraph_subelements (par, par_offset = 0):

    """
    Get the subpar, indent and point spans of a paragraph and return them as a dictionary.
    The start and end character offsets (`par_offset`) of the spans are adjusted accordingly in the `new_start_chat`and `new_end_char` extensions
    to allow for further processing and modifications.
    """

    par_doc = None

    if isinstance(par, str):
        par_text = par
    elif isinstance(par, Span):
        par_text = par.text
    elif isinstance(par, Doc):
        par_text = par.text
        par_doc = par
    else:
        raise TypeError("par must be str, Span or Doc")

    if not par_doc:
        par_doc = blank("en")(par_text)

    # subparagraphs
    subpar_spans = subparagraphs(par_doc)

    subpar_point_spans = []
    subpar_indent_spans = []

    for subpar in subpar_spans:
        # points
        subpar_point_spans.append(points(subpar))
        subpar_indent_spans.append(indents(subpar))

    # adjust paragraph offsets
    if not Span.has_extension('new_start_char'):
        Span.set_extension("new_start_char", default=None, force=True)
    if not Span.has_extension('new_end_char'):
        Span.set_extension("new_end_char", default=None, force=True)

    for subpar in subpar_spans:
        subpar._.new_start_char = subpar.start_char + par_offset
        subpar._.new_end_char = subpar.end_char + par_offset
    for subpar_point in subpar_point_spans:
        for point in subpar_point:
            point._.new_start_char = point.start_char + par_offset
            point._.new_end_char = point.end_char + par_offset
    for subpar_indent in subpar_indent_spans:
        for indent in subpar_indent:
            indent._.new_start_char = indent.start_char + par_offset
            indent._.new_end_char = indent.end_char + par_offset

    return {
        'subpars': subpar_spans,
        'points': subpar_point_spans,
        'indents': subpar_indent_spans
    }


def process_article_elements_modifications(article_elements, article_text, old_char_offset, new_char_offset):

    """Process modifications of article elements and return the replacement text and the new article elements.

    Parameters
    ----------
    article_elements : dict
        The article elements to process.
    article_text : str
        The article text.
    old_char_offset : int
        The old character offset.
    new_char_offset : int
        The new character offset.

    """

    def update_all_char_pos(pos, change):
        """
        Update the char_pos of all article elements that come after.
        """

        for span in spans:
            if span.has_extension('char_pos') and span._.char_pos is not None and span._.char_pos >= pos:
                span._.char_pos += change



    new_article_elements = {
        'pars': [],
        'subpars': [],
        'points': [],
        'indents': []
    }

    # set added extension
    Span.set_extension("added", default=False, force=True)

    article_char_i = 0

    # get all spans into one big list
    spans = []

    spans.extend(flatten(article_elements['pars']))
    spans.extend(flatten(article_elements['subpars']))
    spans.extend(flatten(article_elements['points']))
    spans.extend(flatten(article_elements['indents']))

    # sort spans by char_pos or start_char
    spans = sorted(spans, key=lambda x: x._.char_pos if (x.has_extension('char_pos') and x._.char_pos) else x.start_char)


    # loop over and process spans
    for span in spans:
        char_pos_adjusted_for_span = False # male sure we only adjust once for each span

        # mainly for testin but just to make sure
        set_extensions(span)

        if span.has_extension('added') and span._.added:
            # span already deleted by other span
            continue
        else:
            # deletion
            if span.has_extension('deleted') and span._.deleted:
                # check if other spans overlap with this one
                span._.added = True
                for other_span in spans:
                    # skip same span
                    if other_span == span:
                        continue
                    elif other_span.has_extension('new_element') and other_span._.new_element:
                        # skip other span if it is a new element
                        continue
                    elif other_span.has_extension('added') and other_span._.added:
                        # skip other span if it has been deleted by another span
                        continue
                    # other span fully contained in span
                    if other_span.start_char >= span.start_char and other_span.end_char <= span.end_char:
                        # delete other span and mark as processed
                        other_span._.deleted = True
                        other_span._.added = True

                        if not char_pos_adjusted_for_span:
                            update_all_char_pos(other_span.start_char, -len(other_span.text))
                            char_pos_adjusted_for_span = True

                    # span fully contained in other span
                    elif other_span.start_char <= span.start_char and other_span.end_char >= span.end_char:
                        other_span._.replace_text(get_element_text(other_span, replace_text=True).replace(span.text, ''), keep_ws=True, deletion_threshold = 2)
                        if other_span._.deleted:
                            other_span._.added = True
                            if not char_pos_adjusted_for_span:
                                # TODO does this need to be len(span.text) or len(get_element_text(span, replace_text=True))? (same below)
                                update_all_char_pos(other_span.start_char, -len(other_span.text))
                                char_pos_adjusted_for_span = True
                        else:
                            if not char_pos_adjusted_for_span:
                                update_all_char_pos(span.start_char, -len(span.text))
                                char_pos_adjusted_for_span = True
                    # span overlaps with other span
                    ## this should not happen as all article elements are non-partially-overlapping
            # replacement
            elif ((span.has_extension('new_element') and not span._.new_element) or not span.has_extension('new_element')) and span.has_extension('replacement_text') and span._.replacement_text and len(span._.replacement_text)>0:
                # check if other spans overlap with this one
                for other_span in spans:
                    # skip same span
                    if other_span == span:
                        continue
                    elif other_span.has_extension('new_element') and other_span._.new_element:
                        # skip other span if it is a new element
                        continue
                    elif other_span.has_extension('added') and other_span._.added:
                        # skip other span if it has been deleted by another span
                        continue
                    elif other_span.has_extension('deleted') and other_span._.deleted:
                        # skip other span if it is to be deleted
                        continue
                    # other span fully contained in span
                    if other_span.start_char >= span.start_char and other_span.end_char <= span.end_char:
                        new_other_span_text = get_element_text(span, replace_text=True)[other_span.start_char - span.start_char:other_span.end_char - span.start_char]
                        # replace text within the span margins in other span
                        other_span._.replace_text(new_other_span_text, keep_ws=True, deletion_threshold = 2)
                        if other_span._.deleted:
                            other_span._.added = True
                            if not char_pos_adjusted_for_span:
                                update_all_char_pos(other_span.start_char, -len(other_span.text))
                                char_pos_adjusted_for_span = True

                        else:
                            # TODO does this work if the same span is replaced multiple times?
                            if not char_pos_adjusted_for_span:
                                update_all_char_pos(other_span.start_char, -len(get_element_text(span, replace_text=True)) + len(new_other_span_text))
                                char_pos_adjusted_for_span = True
                    # span fully contained in other span
                    elif other_span.start_char <= span.start_char and other_span.end_char >= span.end_char:
                        # replace text in other span
                        other_span._.replace_text(get_element_text(other_span, replace_text=True).replace(span.text, get_element_text(span, replace_text=True)), keep_ws=True, deletion_threshold = 2)
                        if other_span._.deleted:
                            other_span._.added = True
                            if not char_pos_adjusted_for_span:
                                # TODO does this need to be len(span.text) or len(get_element_text(span, replace_text=True))? (see also above)
                                update_all_char_pos(other_span.start_char, -len(other_span.text))
                                char_pos_adjusted_for_span = True
                        else:
                            if not char_pos_adjusted_for_span:
                                update_all_char_pos(span.start_char, len(get_element_text(span, replace_text=True)) - len(span.text))
                                char_pos_adjusted_for_span = True
            # addition
            elif span.has_extension('new_element') and span._.new_element:
                # check if the element type is below the paragraph level
                if span._.element_type in ['art_subpar', 'art_point', 'art_indent']:
                    # find the paragraph span that the char_pos is contained in / adjacent to
                    for par in article_elements['pars']:
                        if span._.char_pos >= par.start_char and span._.char_pos <= par.end_char:
                            new_par_text = get_element_text(par, replace_text=True)[:span._.char_pos - par.start_char] + get_element_text(span, replace_text=True) + get_element_text(par, replace_text=True)[span._.char_pos - par.start_char:]
                            par._.replace_text(new_par_text, keep_ws=True, deletion_threshold = 2)
                            update_all_char_pos(span._.char_pos, len(get_element_text(span, replace_text=True)))
    # build the new text from the processed paragraph spans and adding the text in between
    new_text = ""

    # add the text before the first span
    if len(spans) > 0:
        new_text += article_text[:spans[0]._.char_pos - old_char_offset if spans[0].has_extension('char_pos') and spans[0]._.char_pos is not None else spans[0].start_char - old_char_offset]
        article_char_i = spans[0]._.char_pos - old_char_offset if spans[0].has_extension('char_pos') and spans[0]._.char_pos is not None  else spans[0].start_char - old_char_offset
    else:
        new_text += article_text
        return new_text, adjust_article_element_offsets(article_elements, old_char_offset, new_char_offset)

    for par in article_elements['pars']:
        if par.has_extension('added') and par._.added and (not par.has_extension('new_element') or (par.has_extension('new_element') and not par._.new_element)):
            article_char_i += len(par.text)
            # skip this par
            continue
        else:
            # deletion
            if par.has_extension('deleted') and par._.deleted:
                # skip this par
                article_char_i += len(par.text)
                continue
            # addition / replacement
            ## add any text before the par
            new_text += article_text[article_char_i:par._.char_pos - old_char_offset if par.has_extension('char_pos') and par._.char_pos is not None else par.start_char - old_char_offset]

            ## update the new par start char
            par._.new_start_char = new_char_offset + len(new_text)

            ## add the par text
            new_text += get_element_text(par, replace_text=True)

            ## update the new_char_end
            par._.new_end_char = new_char_offset + len(new_text)

            ## update the article char index
            article_char_i += len(par.text)

            ## re-do paragraph-level spans (subpars, indents, points)
            new_article_elements['pars'].append(par)
            par_article_elements = recalculate_paragraph_subelements(get_element_text(par, replace_text=True), par_offset = par._.new_start_char)

            ## update the new article elements
            new_article_elements['subpars'].append(par_article_elements['subpars'])
            new_article_elements['points'].append(par_article_elements['points'])
            new_article_elements['indents'].append(par_article_elements['indents'])

    # if there are no pars, add blank article element lists
    if len(new_article_elements['pars']) == 0:
        new_article_elements['subpars'] = [[]]
        new_article_elements['points'] = [[[]]]
        new_article_elements['indents'] = [[[[]]]]


    ## add the text after the par
    new_text += article_text[article_char_i:]

    return new_text, new_article_elements




