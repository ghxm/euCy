from eucy.utils import is_modified_span, get_element_text, set_extensions
from spacy.tokens import Span

def any_modified_article_elements(article_elements):
    """
    Check if there are any modified article elements in the list of article elements.
    """

    for p_i, p in enumerate(article_elements['pars']):
        if is_modified_span(p):
            return True
        for s_i, s in enumerate(article_elements['subpars'][p_i]):
            if is_modified_span(s):
                return True
            for i_i, i in enumerate(article_elements['indents'][p_i][s_i]):
                if is_modified_span(i):
                    return True
            for p_i, p in enumerate(article_elements['points'][p_i][s_i]):
                if is_modified_span(p):
                    return True

    return False


def process_article_elements_modifications(article_elements, article_text, old_char_offset, new_char_offset):

    """Process modifications of article elements and return the replacement text

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

    # set added extension
    Span.set_extension("added", default=False, force=True)

    article_char_i = 0

    # get all spans into one big list
    spans = []
    for p_i, p in enumerate(article_elements['pars']):
        spans.append(p)
        for s_i, s in enumerate(article_elements['subpars'][p_i]):
            spans.append(s)
            for i_i, i in enumerate(article_elements['indents'][p_i][s_i]):
                spans.append(i)
            for p_i, p in enumerate(article_elements['points'][p_i][s_i]):
                spans.append(p)

    # sort spans by char_pos or start_char
    spans = sorted(spans, key=lambda x: x._.char_pos if (x.has_extension('char_pos') and x._.char_pos) else x.start_char)

    # loop over and process spans
    for span in spans:
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
                    # other span fully contained in span
                    if other_span.start_char <= span.start_char and other_span.end_char <= span.end_char:
                        # delete other span and mark as processed
                        other_span._.deleted = True
                        other_span._.added = True
                    # span fully contained in other span
                    elif other_span.start_char <= span.start_char and other_span.end_char >= span.end_char:
                        other_span._.replace_text(other_span.text.replace(span.text, ''), keep_ws=True, deletion_threshold = 2)
                    # span overlaps with other span
                    ## this should not happen as all article elements are non-partially-overlapping
            # addition / replacement
            elif span.has_extension('replacement_text') and span._.replacement_text and len(span._.replacement_text)>0:
                # check if other spans overlap with this one
                for other_span in spans:
                    # skip same span
                    if other_span == span:
                        continue
                    # other span fully contained in span
                    if other_span.start_char <= span.start_char and other_span.end_char <= span.end_char:
                        new_other_span_text = get_element_text(span, replace_text=True)[other_span.start_char - span.start_char:other_span.end_char - span.start_char]
                        # replace text within the span margins in other span
                        other_span._.replace_text(new_other_span_text, keep_ws=True, deletion_threshold = 2)
                    # span fully contained in other span
                    elif other_span.start_char <= span.start_char and other_span.end_char >= span.end_char:
                        # replace text in other span
                        other_span._.replace_text(other_span.text.replace(span.text, get_element_text(span, replace_text=True)), keep_ws=True, deletion_threshold = 2)

    # build the new text from the processed paragraph spans and adding the text in between
    new_text = ""

    # add the text before the first span
    if len(spans) > 0:
        new_text += article_text[:spans[0].start_char - old_char_offset]
        article_char_i = spans[0].start_char - old_char_offset
    else:
        new_text += article_text
        return new_text

    for par in article_elements['pars']:
        if par.has_extension('added') and par._.added:
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
            new_text += article_text[article_char_i:par.start_char - old_char_offset]

            ## update the new par start char
            par._.new_start_char = new_char_offset + len(new_text)

            ## add the par text
            new_text += get_element_text(par, replace_text=True)

            ## update the new_char_end
            par._.new_end_char = new_char_offset + len(new_text)

            ## update the article char index
            article_char_i += len(par.text)

    ## add the text after the par
    new_text += article_text[article_char_i:]

    return new_text



