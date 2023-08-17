from spacy.tokens import Span, Doc, SpanGroup
import spacy

def modify_doc(doc, nlp = None, add_spans = True, return_doc = True):
    """Modify the original text in the doc to contain the new replacement text (`._.replacement_text`) where applicable.

    Args:
        doc (spacy.tokens.Doc): spaCy doc
        nlp (spacy.lang): spaCy model to use for new doc. If None, `spacy.blank("en")` is used.
        add_spans (bool): If True, add all element non-overlapping attributes/spans from the original doc to the new doc. If False, only the text is modified.
        return_doc (bool): If True, return the new doc. If False, return the new text.

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
        old_spans[group] = doc.spans[group]



    old_text_char_i = 0

    for k, spangroup in old_spans.items():

        for span in spangroup:
            # get replacement text
            replacement_text = span._.replacement_text if span.has_extension('replacement_text') and span._.replacement_text is not None else span.text

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
    for key, spangroup in old_spans.items():

        # add span group
        new_doc.spans[key] = SpanGroup(new_doc, name=key, attrs=spangroup.attrs)


        for span in spangroup:
            if span.has_extension('new_start_char'):
                new_doc.spans[key].append(span._.replacement_span(new_doc))

    # @TODO Hier weiter check which of underscore extenstions, e.g. article elements etc, could be recreated here
    #      -> maybe modify EuWrapper to be able to wokr with pre-annotated docs
    #      -> maybe configure underscore elements (e.g. parts) such that they only refer to spans and auto-update


    return new_doc





    # create new spans






