import re

from spacy.tokens import Doc

from eucy import exceptions
from eucy import regex as eure
from eucy import utils


class Structure:
    """Takes and returns a spacy Doc object storing its text parts (citations, recitals, enacting terms) in _.parts"""

    def __init__(self):

        if not Doc.has_extension("parts"):
            Doc.set_extension("parts", default=None)

    def __call__(self, doc):
        """Split the document into its parts and store them in _.parts

        Parameters
        ----------
        doc: spacy.tokens.Doc
            the document to be split

        Returns
        -------
        spacy.tokens.Doc
            the document with the parts stored in _.parts

        """

        # split it and store parts
        doc._.parts = text_parts(doc)

        return doc


def text_parts(doc):

    char_token = utils.chars_to_tokens_dict(doc)

    # function to map char ids to token ids
    def _to_token(char):
        token = char_token.get(char, None)
        while token is None:
            char = char - 1
            token = char_token.get(char - 1, None)
            if char < 1:
                token = 0
        return token

    # return dict of spans of text elements

    citations = None
    recitals = None
    enacting = None
    enacting_with_toc = None
    annex = None

    text = doc.text
    text_end_char = len(text)

    front_end_match = None

    # first, try to split the text in the the middle, right before the enacting terms
    while True:

        # normal
        enacting_start_match = re.search(eure.structure['enacting_start'],
                                         text,
                                         flags=re.MULTILINE)

        if enacting_start_match is not None:
            break

        # try a more lenient version
        enacting_start_match = re.search(
            eure.structure['enacting_start_lenient'], text, flags=re.MULTILINE)

        if enacting_start_match is not None:
            break

        # if all else fails: try to match right before the first
        enacting_start_match = re.search(eure.structure['article_start'],
                                         text,
                                         flags=re.IGNORECASE | re.MULTILINE)

        if enacting_start_match is not None:
            break
        else:
            raise exceptions.StructureException(
                "Text does not appear to be in a format that can be handled by this function."
            )

    front = doc[_to_token(0):_to_token(enacting_start_match.end())]
    middle = doc[_to_token(enacting_start_match.end()):_to_token(text_end_char
                                                                 )]

    # try to split the middle part to separate the back matter

    middle_end_match = None

    while True:

        # Normal version with "Done at"

        middle_end_match = re.search(eure.structure['done_at_start'],
                                     middle.text,
                                     flags=re.MULTILINE | re.IGNORECASE)

        if middle_end_match is not None:
            break

        middle_end_match = re.search(eure.structure['annex_start'],
                                     middle.text,
                                     flags=re.MULTILINE | re.IGNORECASE)

        if middle_end_match is not None:
            break

        # last resort: look for the last article position and match a shortened version of the middle text for some indicators that the enacting terms are done

        try:
            pos_last_article = \
            [m.start () for m in re.finditer (eure.structure['article_start'], middle.text, flags=re.MULTILINE | re.IGNORECASE)][-1]
        except:
            len_enacting = float(len(middle.text))
            pos_last_article = int(len_enacting - 0.1 * len_enacting)

        pos_last_article = middle.start_char + pos_last_article

        # this regex makes sure there's at least pos_last_article before the group matches
        middle_end_match = re.search(
            f'(?<=.{{{pos_last_article}}}).*?(^)(?=(?:[\(\[][0-9]+[\)\]])|(?:[A-Z]{{3,}}))',
            text,
            flags=re.DOTALL | re.MULTILINE)

        if middle_end_match is None:
            break
        else:
            middle_end_match = middle_end_match.group(1)
            break

    if middle_end_match is not None:
        middle = doc[_to_token(middle.start_char
                               ):_to_token(middle.start_char +
                                           middle_end_match.end())]
        back = doc[_to_token(middle.start_char +
                             middle_end_match.end()):_to_token(text_end_char)]
    else:
        back = None

    # Split front into Explanatory Memorandum and Citations and Recitals

    front_matter_end_match = None

    no_citations = False
    no_recitals = False

    while True:

        expl_memo_start_matches = [
            m for m in re.finditer(r'(?=explanatory\s*memorandum)',
                                   front.text,
                                   flags=re.IGNORECASE)
        ]

        law_start_pos = None

        if len(expl_memo_start_matches) > 0:

            # match proposal start after explanatory meorandum match (to make sure, we're not capturing the "proposal for a " in the title)
            proposal_start_match = re.search(
                f'(?<=.{{{expl_memo_start_matches[-1].end()}}}).*?{eure.structure["proposal_start"]}',
                front.text,
                flags=re.MULTILINE | re.IGNORECASE | re.DOTALL)
            law_start_match = re.search(
                f'(?<=.{{{expl_memo_start_matches[-1].end()}}}).*?{eure.structure["proposal_law_start"]}',
                front.text,
                flags=re.MULTILINE | re.IGNORECASE | re.DOTALL)

            if proposal_start_match is not None:
                law_start_pos = proposal_start_match.end()
            elif law_start_match is not None:
                law_start_pos = law_start_match.end()

        if law_start_pos is None:
            law_start_pos = 0

        front_matter_end_match = re.search(
            f'(?<=.{{{law_start_pos}}}).*?' +
            eure.structure['citations_start'], front.text,
            re.MULTILINE | re.DOTALL)

        if front_matter_end_match is not None:
            break

        front_matter_end_match = re.search(
            eure.structure['citations_start'], front.text,
            re.MULTILINE | re.IGNORECASE)  # more relaxed version ignoring case

        if front_matter_end_match is not None:
            break

        # if no citations
        no_citations = True

        front_matter_end_match = re.search(
            eure.structure['recitals_start_whereas'], front.text,
            re.MULTILINE | re.IGNORECASE)  # look for recitals

        if front_matter_end_match is not None:
            break

        if front_matter_end_match is None:
            front_matter_end_match = re.search(
                eure.structure['recitals_start_having'], front.text,
                re.MULTILINE | re.IGNORECASE
            )  # look for introdcued with "having regard to the following"

        if front_matter_end_match is not None:
            break
        else:
            no_recitals = True
            break

    if no_citations and not no_recitals:
        recitals = doc[_to_token(front_matter_end_match.end()):front.end]

    if no_recitals and not no_citations:
        citations = doc[_to_token(front_matter_end_match.end()):front.end]

    # if both recitals and citations exist (otherwise they would have been set above)
    if (recitals is None and not no_recitals) and (citations is None
                                                   and not no_citations):

        recitals_start_match = None

        # look for recitals
        while True:

            recitals_start_match = re.search(
                f'(?<=.{{{front_matter_end_match.start()}}}).*?' +
                eure.structure['recitals_start_whereas'], front.text,
                re.MULTILINE | re.IGNORECASE | re.DOTALL)  # look for recitals

            if recitals_start_match is not None:
                break

            recitals_start_match = re.search(
                f'(?<=.{{{front_matter_end_match.start()}}}).*?' +
                eure.structure['recitals_start_having'], front.text,
                re.MULTILINE | re.IGNORECASE | re.DOTALL
            )  # look for introdcued with "having regard to the following"

            if recitals_start_match is not None:
                break

            # there's a possibility the recitals were captured as citations if they're not introduced with "whereas" or "having regard to the following"
            # in this case, we need to remove them from the citations

            # search for the start of a recital
            for reg in [
                    eure.elements['recital_num_start'],
                    eure.elements['recital_whereas_start']
            ]:
                recitals_start_match = re.search(
                    f'(?<=.{{{front_matter_end_match.start()}}}).*?' + reg,
                    front.text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                if recitals_start_match is not None:
                    break

            if recitals_start_match is not None:
                break
            else:
                no_recitals = True  # if there are no recitals, but for whatever reason this has not been detected yet
                break

        if not no_recitals:
            recitals = doc[_to_token(recitals_start_match.end()):front.end]

        citations_start_match = None

        # look for citations
        while True:

            citations_start_match = re.search(
                f'(?<=.{{{front_matter_end_match.start()}}}).*?' +
                eure.structure['citations_start'], front.text,
                re.MULTILINE | re.IGNORECASE | re.DOTALL)  # look for citations

            if citations_start_match is not None:
                break
            else:
                no_citations = True
                break

        if not no_citations:
            if recitals_start_match is None:
                citations = doc[_to_token(citations_start_match.end()):front.
                                end]
            else:
                citations = doc[_to_token(citations_start_match.end(
                )):_to_token(recitals_start_match.end())]

    # @TODO: Annex
    # annex_start_match = re.search(r'^(?=\s*(?:ANNEX|LEGISLATIVE FINANCIAL STATEMENT)[\s])', back, flags = re.MULTILINE|re.IGNORECASE)[1]

    enacting = middle
    enacting_with_toc = enacting

    enacting_toc_start_match = re.search(eure.structure['toc_start'],
                                         enacting.text[:len(enacting.text) //
                                                       4],
                                         flags=re.MULTILINE | re.IGNORECASE)
    if recitals is not None:
        recitals_toc_start_match = re.search(eure.structure['toc_start'],
                                             recitals.text,
                                             flags=re.MULTILINE
                                             | re.IGNORECASE)

    # remove TOC and store in enacting (vs enacting_with_toc), if no TOC enacting = enacting_with_toc
    ## if 'TALBE OF CONTENTS' in first quarter of enacting
    if bool(enacting_toc_start_match):

        # identify start of first article, but exclude the first few lines in case Article 1 is part of the TOC
        article_1_start_match = re.search(
            eure.structure['article_1_start'],
            enacting.text[100:len(enacting.text) // 4],
            flags=re.MULTILINE | re.IGNORECASE)

        if article_1_start_match is not None:
            enacting = enacting[
                utils.char_to_token(100 +
                                    article_1_start_match.start(), enacting):]

            # enacting = enacting[_to_token (100 + article_1_start_match.start ()):] @TODO: why won't this work?

    elif recitals is not None and bool(
            recitals_toc_start_match
    ):  # in case the TOC is part of recitals bc of previous split
        recitals = recitals.char_span(0, recitals_toc_start_match.end())
        if recitals is None:
            toc_start = citations.end
        elif recitals is not None:
            toc_start = recitals.end
        else:
            toc_start = enacting.start
        enacting_with_toc = doc[toc_start:enacting.end]

    return ({
        'citations': citations,
        'recitals': recitals,
        'enacting': enacting,
        'enacting_with_toc': enacting_with_toc,
        'annex': annex
    })
