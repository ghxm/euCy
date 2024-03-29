"""Main module."""

import warnings
from collections import Counter

from spacy.language import Language
from spacy.pipeline.dep_parser import DEFAULT_PARSER_MODEL
from spacy.tokens import Doc

from eucy import content, elements, entities, structure
from eucy.entities import references
from eucy.tokenizer import retokenizer, tokenizer
from eucy.utils import (get_element_by_match, get_element_by_num,
                        set_extensions, timeout)


class EuWrapper:
    """EuCy wrapper class for a spacy Language object
        (not a real pipeline component)"""

    def __init__(self, nlp, debug=False):
        """
        Initialize EuWrapper object


        Parameters
        ----------
        nlp : spacy Language object
            Spacy Language object to be wrapped
        debug : bool, optional
            Whether to print debug information, by default False


        """

        if not isinstance(nlp, Language):
            raise TypeError("nlp must be a spacy Language object")

        nlp.tokenizer = tokenizer(nlp)
        nlp.add_pipe("retokenizer", last=True, name="retokenizer")

        self.debug = debug

        # @TODO add retokenizer pipe after tokenizer

        self.nlp = nlp

        self.EuStructure = structure.Structure()
        self.EuElements = elements.Elements()

        self.EuReferenceSearch = entities.EntitySearch(
            name="references",
            nlp=self.nlp,
            matcher=references.ReferenceMatcher,
            overwrite_ents=True,
            debug=self.debug)

        # Register extensions
        set_extensions()

        #

        # Span.set_extension("parent_elements", default = None, getter = "") # @TODO assign function to check whether span is encased by other spans and return their attributes as dict in list

    @timeout(180)
    def __call__(self, doc):
        """
        Call EuCy wrapper on a spacy Doc object and add EU law specific attributes to the doc object. Add `SpanGroup` objects (`spans` attribute) and fills various custom extensions (`_` attribute) to the doc object.

        Parameters
        ----------
        doc : spacy Doc object

        Returns
        -------
        spacy Doc object with added attributes
        """

        # if possible, check if doc or string is passed and convert to doc if string
        if isinstance(doc, str):
            doc = self.nlp(doc)
        elif not isinstance(doc, Doc):
            raise TypeError("doc must be a spacy Doc object or a string")

        doc._.title = content.find_title(doc)

        if (len(doc.text.strip()) - len(doc._.title.strip())) < 500:
            doc._.no_text = True

        if not doc._.no_text:
            if doc._.parts is None and hasattr(self, 'EuStructure'):
                doc = self.EuStructure(doc)
            elif doc._.parts is not None:
                pass
            else:
                warnings.warn("doc object does not have Structure Component.")

            if doc._.article_elements is None:
                doc = self.EuElements(doc)

            doc = self.EuReferenceSearch(doc)
            if doc._.complexity is None:
                # get complexity measures
                doc._.complexity = {
                    'citations': citation_count(doc),
                    'recitals': recital_count(doc),
                    'articles': article_count(doc),
                    'structural_size': structural_size(doc, "all"),
                    'structural_size_enacting':
                    structural_size(doc, "enacting"),
                    'references': reference_count(doc),
                    'avg_depth': avg_depth(doc, basis='element'),
                    'avg_article_depth': avg_depth(doc, basis='article'),
                    'words_noannex': word_count(doc, annex=False)
                }

        return doc


def citation_count(doc):

    if not 'citations' in doc.spans:
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    return (len(doc.spans['citations']))


def recital_count(doc):

    if not 'recitals' in doc.spans:
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    return (len(doc.spans['recitals']))


def count_articles():

    raise NotImplementedError

    # @TODO: various methods for article counting (see older analysis)
    pass


def matched_articles_count(doc):
    if not doc.has_extension("parts") or not doc.has_extension(
            "article_elements"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    return (len(doc.spans['articles']))


def last_matched_article_num(doc):

    raise NotImplementedError

    if not doc.has_extension("parts") or not doc.has_extension(
            "article_elements"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    # @TODO (see older analysis)
    pass


def article_count(doc):
    if not doc.has_extension("parts") or not doc.has_extension(
            "article_elements"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    # @TODO methods in older analysis
    ## using distance measures

    return (matched_articles_count(doc))


def structural_size(doc, parts="all"):

    if not doc.has_extension("parts") or not doc.has_extension(
            "article_elements"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    enacting_size = 0

    # loop over articles
    for article in doc._.article_elements:
        # loop over (sub)paragraphs in article
        for subpar, subparpoints, subparindents in zip(article['subpars'],
                                                       article['points'],
                                                       article['indents']):
            enacting_size += len(subpar)

            for indents, points in zip(subparindents, subparpoints):
                enacting_size += len(indents)
                enacting_size += len(points)

    if parts == "enacting":
        return enacting_size
    else:
        recital_size = recital_count(doc)
        return enacting_size + recital_size


def avg_depth(doc, basis="element"):

    if not doc.has_extension("parts") or not doc.has_extension(
            "article_elements"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    depths = {1: 0, 2: 0, 3: 0}

    articles_levels = []

    # loop over articles
    for article in doc._.article_elements:
        # loop over (sub)paragraphs in article

        article_levels = []

        # set the paragraph level (1 if single paragraph, 2 if more)
        if len(article['subpars']) > 1:
            par_level = 2
        else:
            par_level = 1

        for i, (subpar, subparpoints, subparindents) in enumerate(
                zip(article['subpars'], article['points'],
                    article['indents'])):

            article_levels.append(par_level)

            for indents, points in zip(subparindents, subparpoints):
                indents_level = par_level + 1
                points_level = indents_level

                for indent in indents:
                    article_levels.append(indents_level)

                for point in points:
                    article_levels.append(points_level)

        articles_levels.append(article_levels)

    try:

        if basis == "article":
            # average article depth
            if len(articles_levels) == 0:
                return None
            else:
                return sum([
                    sum(lvl) / len(lvl)
                    for lvl in articles_levels if len(lvl) != 0
                ]) / len(articles_levels)
        elif basis == "element":
            # average element depth
            if len(articles_levels) == 0:
                return None
            else:
                return sum([sum(lvl) for lvl in articles_levels]) / sum(
                    [len(l) for l in articles_levels])
    except:
        return None


def reference_count(doc):

    if not doc.has_extension("parts") or not doc.has_extension(
            "article_elements"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    ref_count = Counter()
    ref_count['internal'] = 0
    ref_count['external'] = 0

    for ent in doc.ents:
        if ent.label_ == "REFERENCE":
            for ref in ent._.references:
                ref_count[ref.get('relation', 'NONE')] += 1

    return ref_count


def word_count(doc, annex=False):
    if not doc.has_extension("parts"):
        # if function is called outside spacy pipeline

        EuDoc = EuWrapper

        doc = EuDoc(doc)

    word_count = sum([len(r) for r in doc.spans['recitals']]) + sum([
        len(c) for c in doc.spans['citations']
    ]) + sum([len(a) for a in doc.spans['articles']])

    if annex:
        word_count += len(doc.spans['annex'])

    return word_count
