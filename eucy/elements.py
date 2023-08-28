import re

from spacy.tokens import Doc
from spacy.tokens.span import Span

from eucy import regex as eure
from eucy import structure, utils


class Elements:

    def __init__(self):

        # Set Doc-level element extions
        if not Doc.has_extension("article_elements"):
            Doc.set_extension("article_elements", default=None)

        if not Doc.has_extension("parts"):
            self.EuStructure = structure.Structure()

        # Set Span-level element extensions
        if not Span.has_extension("element_type"):
            Span.set_extension("element_type", default=None)
            Span.set_extension("element_pos",
                               default=None)  # the index of an element
            Span.set_extension(
                "element_num", default=None
            )  # the number an element has been assigned in the text
            Span.set_extension(
                "element_numstr", default=None
            )  # the number an element has been assigned in the text

    def __call__(self, doc, overwrite=False):
        """Apply the pipeline component to a `Doc` object.
        doc (Doc): The `Doc` returned by the previous pipeline component.
        RETURNS (Doc): The modified `Doc` object.
        """

        if doc._.parts is None:

            doc = self.EuStructure(doc)

        # Add SpanGroup for ...

        if doc.spans.get(
                'citations'
        ) is None or overwrite:  # in case a pre-coded (e.g. modified) doc is passed
            ## Citations
            doc.spans['citations'] = citations(doc._.parts['citations'])

        if doc.spans.get('recitals') is None or overwrite:
            ## Recitals
            doc.spans['recitals'] = recitals(doc._.parts['recitals'])

        if doc.spans.get('articles') is None or overwrite:
            ## Articles
            doc.spans['articles'] = articles(doc._.parts['enacting'])

        doc._.article_elements = []

        for article in doc.spans['articles']:
            doc._.article_elements.append(article_elements(article))

        return doc


def citations(doc_citations):

    citations = utils._part_argument_check(doc_citations, 'citations')

    if citations is None:
        return []

    char_token = utils.chars_to_tokens_dict(citations,
                                            input="as_ref",
                                            output="as_ref")

    citation_matches = []

    while True:

        citation_matches = [
            m for m in re.finditer(eure.elements['citation'],
                                   doc_citations.text,
                                   flags=re.MULTILINE)
        ]

        if len(citation_matches) > 0:
            break

        # try again ignoring case
        citation_matches = [
            m for m in re.finditer(eure.elements['citation'],
                                   doc_citations.text,
                                   flags=re.MULTILINE | re.IGNORECASE)
        ]

        break

    citation_matches = [ma for ma in citation_matches if len(ma.group(0)) > 4]

    if isinstance(doc_citations, Doc):
        citation_list = [
            doc_citations.char_span.char_span(mat.start(),
                                              mat.end(),
                                              alignment_mode="expand")
            for mat in citation_matches
        ]
    else:
        citation_list = [
            doc_citations[
                utils.char_to_token(mat.start(), char_token):utils.
                char_to_token(mat.end(), char_token, alignment_mode="expand")]
            for mat in citation_matches
        ]

    if Span.has_extension("element_type"):
        for i, c in enumerate(citation_list):
            citation_list[i]._.element_type = "citation"

    return citation_list


def recitals(doc_recitals):

    recitals = utils._part_argument_check(doc_recitals, 'recitals')

    if recitals is None:
        return []

    char_token = utils.chars_to_tokens_dict(recitals,
                                            input="as_ref",
                                            output="as_ref")

    def get_recitals(recital_matches):
        recital_matches_pos = [
            (m.start(),
             recital_matches[i +
                             1].start()) if i < len(recital_matches) - 1 else
            (m.start(), len(recitals.text))
            for i, m in enumerate(recital_matches)
        ]

        if isinstance(doc_recitals, Doc):
            recital_list = [
                doc_recitals.char_span.char_span(mat[0],
                                                 mat[1],
                                                 alignment_mode="expand")
                for mat in recital_matches_pos
            ]
        else:
            recital_list = [
                doc_recitals[
                    utils.char_to_token(mat[0], char_token):utils.
                    char_to_token(mat[1], char_token, alignment_mode="expand")]
                for mat in recital_matches_pos
            ]

        return recital_list

    recital_matches = []

    recital_list = []

    while True:

        # @TODO differentiate between parentheses recitals and dot recitals and, in case of mixed captures, decide which to use (e.g. 52017PC0603)
        # @TODO catch recitals with multiple paragraphs completely (cf. example_1.txt)

        recital_matches_num = [
            m for m in re.finditer(eure.elements['recital_num_start'],
                                   recitals.text, re.MULTILINE)
        ]

        recitals_parentheses = []
        recitals_dot = []
        recitals_other = []

        # try to filter out bad matches by checking for the type (parentheses, dot, other)
        for match in recital_matches_num:
            if re.search(r'^[\s\(]*[0-9]+\s*\)', match.group(0)) is not None:
                recitals_parentheses.append(match)
            elif re.search(r'^[\s]*[0-9]+\s*\.', match.group(0)) is not None:
                recitals_dot.append(match)
            else:
                recitals_other.append(match)

        # if there are only parentheses recitals, use them
        if len(recitals_parentheses) > 0 and len(recitals_parentheses) > len(
                recitals_dot) and len(recitals_parentheses) > len(
                    recitals_other) == 0:
            recital_matches_num = recitals_parentheses
        # @TODO maybe use a more refined approach including dot recitals / other recitals if they are not too far away from the parentheses recitals

        recital_list = get_recitals(recital_matches_num)

        # remove recitals with less than 10 words
        recital_list = [rec for rec in recital_list if len(rec) > 6]

        if len(recital_list) > 0:
            break

        # if none found yet, try for unnumbered recirals starting with whereas
        recital_matches_whereas = [
            ma for ma in re.finditer(eure.elements['recital_whereas_start'],
                                     recitals.text,
                                     flags=re.MULTILINE | re.IGNORECASE)
        ]

        recital_list = get_recitals(recital_matches_whereas)

        # remove recitals with less than 6 words
        recital_list = [rec for rec in recital_list if len(rec) > 6]

        if len(recital_list) > 0:
            break

        # if none  found yet, search for normal paragraph recitals
        recital_matches_par = [
            ma for ma in re.finditer(eure.elements['recital_par_start'],
                                     recitals.text,
                                     flags=re.MULTILINE | re.IGNORECASE)
        ]

        recital_list = get_recitals(recital_matches_par)

        # remove recitals with less than 6 words
        recital_list = [rec for rec in recital_list if len(rec) > 6]

        if len(recital_list) > 0:
            break

    if Span.has_extension("element_type"):
        for i, c in enumerate(recital_list):
            recital_list[i]._.element_type = "recital"

    return recital_list


def articles(doc_articles):

    articles = utils._part_argument_check(doc_articles, 'enacting')

    if articles is None:
        return []

    char_token = utils.chars_to_tokens_dict(articles,
                                            input="as_ref",
                                            output="as_ref")

    article_id_matches = []

    while True:

        article_id_matches = [
            m for m in re.finditer(eure.elements['article_identifier'],
                                   articles.text,
                                   flags=re.MULTILINE | re.IGNORECASE)
        ]

        if len(article_id_matches) > 0:
            break

        # test for single article
        article_id_matches = [
            m for m in re.finditer(eure.elements['single_article_identifier'],
                                   articles.text,
                                   flags=re.MULTILINE | re.IGNORECASE)
        ]

        if len(article_id_matches) == 1:
            break

        # @TODO: handle cases where neither normal nor sinngle article identifier regexes match

        break

    article_id_matches = [
        ma for ma in article_id_matches if len(ma.group(0)) > 4
    ]

    article_list = []

    for i, m in enumerate(article_id_matches, start=0):

        # match text of entire article
        article_start = m.start()

        if i < len(article_id_matches) - 1:
            article_end = article_id_matches[i + 1].start()
        else:
            article_end = len(doc_articles.text)

        if isinstance(doc_articles, Doc):
            article_span = doc_articles.char_span.char_span(
                article_start, article_end, alignment_mode="expand")
        else:
            article_span = doc_articles[utils.char_to_token(
                article_start, char_token):utils.char_to_token(
                    article_end, char_token, alignment_mode="expand")]

        # set extensions
        if article_span.has_extension("element_pos"):
            article_span._.element_pos = i + 1
        if article_span.has_extension("element_numstr"):

            article_nums = []

            while True:

                article_nums = [
                    m.group(1)
                    for m in re.finditer(eure.elements['article_num'],
                                         article_span.text.strip(),
                                         flags=re.IGNORECASE)
                ]

                if len(article_nums) > 0:
                    break

                article_nums = [
                    ma.group(0)
                    for ma in re.finditer(eure.elements['article_any_num'],
                                          article_span.text.strip())
                ]

                break

            if len(article_nums) > 1:
                article_numstr = article_nums[0].strip()
            else:
                article_numstr = None

            article_span._.element_numstr = article_numstr

        article_list.append(article_span)

    if Span.has_extension("element_type"):
        for i, a in enumerate(article_list):
            article_list[i]._.element_type = "article"

    return article_list


def article_elements(doc_article):
    """Mark up an article, inlcuding Title, Paragraph, Point, etc...
    """

    if not isinstance(doc_article, (Doc, Span)):
        raise TypeError(
            str(type(doc_article)) +
            " type not supported. Please pass a Doc or Span object.")

    def _paragraphs(article):

        par_char_token = utils.chars_to_tokens_dict(article,
                                                    input="as_ref",
                                                    output="as_ref")

        par_start_matches = []

        par_start_matches = [
            m for m in re.finditer(eure.elements['article_num_paragraph'],
                                   article.text,
                                   flags=re.MULTILINE)
        ]

        unnum_pars = False

        if len(par_start_matches) == 0:
            par_start_matches = [
                ma
                for ma in re.finditer(eure.elements['article_unnum_paragraph'],
                                      article.text,
                                      flags=re.MULTILINE | re.DOTALL)
            ]
            unnum_pars = True

        par_list = []

        for i, m in enumerate(par_start_matches, start=0):

            # match text of entire article
            if unnum_pars and len(m.groups()) > 0:
                par_start = m.start(1)
            else:
                par_start = m.start()

            if i < len(par_start_matches) - 1:
                if unnum_pars and len(m.groups()) > 0:
                    par_end = par_start_matches[i + 1].start(1)
                else:
                    par_end = par_start_matches[i + 1].start()
            else:
                par_end = len(article.text)

            if isinstance(article, Doc):
                par_span = article.char_span(par_start,
                                             par_end,
                                             alignment_mode="expand")
            else:
                par_span = article[utils.char_to_token(
                    par_start, par_char_token):utils.char_to_token(
                        par_end, par_char_token, alignment_mode="expand")]

            # set extensions
            if par_span.has_extension("element_pos"):
                par_span._.element_pos = i + 1
            if par_span.has_extension("element_numstr"):
                if len(m.groups()) > 0:
                    par_span._.element_numstr = m.group(1)

            par_list.append(par_span)

        if Span.has_extension("element_type"):
            for i, a in enumerate(par_list):
                par_list[i]._.element_type = "art_par"

        # if no paragraphs found, set article as par
        if len(par_list) == 0 and len(article.text.strip()) > 1:
            par_list.append(article)
            if Span.has_extension("element_type"):
                for i, a in enumerate(par_list):
                    par_list[i]._.element_type = "art_par"
        return par_list

    def _subparagraphs(par):
        """find and return all subpar spans (always unnumbered). Each par has at least one subpar."""

        subpar_char_token = utils.chars_to_tokens_dict(par,
                                                       input="as_ref",
                                                       output="as_ref")

        subpar_start_matches = []

        # mtch each par so that each par has at least one subpar
        subpar_start_matches = [
            m for m in re.finditer(eure.elements['article_subpar_start'],
                                   par.text,
                                   flags=re.MULTILINE)
        ]

        subpar_list = []

        for i, m in enumerate(subpar_start_matches, start=0):

            # match text of entire par
            subpar_start = m.start()

            if i < len(subpar_start_matches) - 1:
                subpar_end = subpar_start_matches[i + 1].start()
            else:
                subpar_end = len(par.text)

            if isinstance(par, Doc):
                subpar_span = par.char_span(subpar_start,
                                            subpar_end,
                                            alignment_mode="expand")
            else:
                subpar_span = par[utils.char_to_token(
                    subpar_start, subpar_char_token):utils.char_to_token(
                        subpar_end, subpar_char_token, alignment_mode="expand"
                    )]

            # sort out chpater/section titles
            if len(subpar_span.text.strip()) < 200 and bool(
                    re.search(eure.elements['article_section_titles'],
                              subpar_span.text,
                              flags=re.IGNORECASE | re.MULTILINE)):
                continue

            # set extensions
            if subpar_span.has_extension("element_pos"):
                subpar_span._.element_pos = i + 1

            subpar_list.append(subpar_span)

        if Span.has_extension("element_type"):
            for i, a in enumerate(subpar_list):
                subpar_list[i]._.element_type = "art_subpar"

        return subpar_list

    def _points(subpar):

        point_char_token = utils.chars_to_tokens_dict(subpar,
                                                      input="as_ref",
                                                      output="as_ref")

        point_start_matches = []

        # mtch each subpar so that each subpar has at least one point
        point_start_matches = [
            m for m in re.finditer(eure.elements['article_point_id'],
                                   subpar.text,
                                   flags=re.MULTILINE)
        ]

        point_list = []

        for i, m in enumerate(point_start_matches, start=0):

            # match text of entire subpar
            point_start = m.start()

            if i < len(point_start_matches) - 1:
                point_end = point_start_matches[i + 1].start()
            else:
                point_end = len(subpar.text)

            if isinstance(subpar, Doc):
                point_span = subpar.char_span(point_start,
                                              point_end,
                                              alignment_mode="expand")
            else:
                point_span = subpar[utils.char_to_token(
                    point_start, point_char_token):utils.char_to_token(
                        point_end, point_char_token, alignment_mode="expand")]

            # set extensions
            if point_span.has_extension("element_pos"):
                point_span._.element_pos = i + 1
            if point_span.has_extension("element_numstr"):
                point_span._.element_numstr = m.group(0)

            point_list.append(point_span)

        if Span.has_extension("element_type"):
            for i, a in enumerate(point_list):
                point_list[i]._.element_type = "art_point"

        return point_list

    def _indents(subpar):

        indent_char_token = utils.chars_to_tokens_dict(subpar,
                                                       input="as_ref",
                                                       output="as_ref")

        indent_start_matches = []

        # mtch each subpar so that each subpar has at least one indent
        indent_start_matches = [
            m for m in re.finditer(eure.elements['article_indent_id'],
                                   subpar.text,
                                   flags=re.MULTILINE)
        ]

        indent_list = []

        for i, m in enumerate(indent_start_matches, start=0):

            # match text of entire subpar
            indent_start = m.start()

            if i < len(indent_start_matches) - 1:
                indent_end = indent_start_matches[i + 1].start()
            else:
                indent_end = len(subpar.text)

            if isinstance(subpar, Doc):
                indent_span = subpar.char_span(indent_start,
                                               indent_end,
                                               alignment_mode="expand")
            else:
                indent_span = subpar[utils.char_to_token(
                    indent_start, indent_char_token
                ):utils.char_to_token(
                    indent_end, indent_char_token, alignment_mode="expand")]

            # set extensions
            if indent_span.has_extension("element_pos"):
                indent_span._.element_pos = i + 1

            indent_list.append(indent_span)

        if Span.has_extension("element_type"):
            for i, a in enumerate(indent_list):
                indent_list[i]._.element_type = "art_indent"

        return indent_list

    # Paragraphs
    par_spans = _paragraphs(doc_article)

    par_subpar_spans = []

    par_subpar_point_spans = []
    par_subpar_indent_spans = []

    for par in par_spans:
        # subparagraphs
        subpar_spans = _subparagraphs(par)

        par_subpar_spans.append(subpar_spans)

        subpar_point_spans = []
        subpar_indent_spans = []

        for subpar in subpar_spans:
            # points
            subpar_point_spans.append(_points(subpar))
            subpar_indent_spans.append(_indents(subpar))

        par_subpar_point_spans.append(subpar_point_spans)
        par_subpar_indent_spans.append(subpar_indent_spans)

    return {
        'pars': par_spans,
        'subpars': par_subpar_spans,
        'points': par_subpar_point_spans,
        'indents': par_subpar_indent_spans
    }
