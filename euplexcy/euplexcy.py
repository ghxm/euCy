"""Main module."""

from spacy.tokens import Doc, Span
from euplexcy import structure
from euplexcy import elements
from euplexcy import content
from euplexcy import entities
from euplexcy.entities import references
from euplexcy.tokenizer import tokenizer, retokenizer
from collections import Counter
from spacy.pipeline.dep_parser import DEFAULT_PARSER_MODEL
import en_core_web_sm


class EuplexWrapper:

    # Spacy pipeline component
    # (Parts called here can also be used inidividually and without the pipeline functonality)
    # but this is a wrapepr for them

    # EUPLEX version of a Spacy Doc obbjects that extends it by
    # a structure attribute/funciton (that stores infromation that calls resp spacy tokennts e/attributes)
    # a complexity attribute that provides statistics on the computed values from various package functions
    # (by supplying an EuplexDoc obbject to a pakage function, it can use the additional information to make better inference)
    # class to run all analyses on a
    # returnns a combination of a spacy object and some additional information

    def __init__(self, nlp, debug = False):

        nlp.tokenizer = tokenizer (nlp)
        nlp.add_pipe("retokenizer", last = True, name = "retokenizer")

        self.debug = debug

        # @TODO add retokenizer pipe after tokenizer

        self.nlp = nlp

        if not Doc.has_extension("parts"):
            self.EuplexStructure = structure.Structure()
        if not Doc.has_extension("article_elements"):
            self.EuplexElements = elements.Elements()

        self.EuplexReferenceSearch = entities.EntitySearch(name = "references", nlp = self.nlp, matcher = references.ReferenceMatcher, overwrite_ents=True, debug=self.debug)

        # Register extensions
        if not Doc.has_extension("complexity"):
            Doc.set_extension("complexity", default = None)

        if not Doc.has_extension("readability"):
            Doc.set_extension("readability", default = None)

        if not Doc.has_extension("title"):
            Doc.set_extension ("title", default=None)
            Doc.set_extension ("no_text", default=False)

        # Span.set_extension("parent_elements", default = None, getter = "") # @TODO assign function to check whether span is encased by other spans and return their attributes as dict in list


    def __call__(self, doc):
        """Apply the pipeline component to a `Doc` object.
        doc (Doc): The `Doc` returned by the previous pipeline component.
        RETURNS (Doc): The modified `Doc` object.
        """

        doc._.title = content.find_title (doc)

        if (len (doc.text.strip ()) - len (doc._.title.strip ())) < 500:
            doc._.no_text = True

        if not doc._.no_text:
            if doc._.parts is None:
                doc = self.EuplexStructure(doc)
            if doc._.article_elements is None:
                doc = self.EuplexElements(doc)
            doc = self.EuplexReferenceSearch(doc)
            if doc._.complexity is None:
                # get complexity measures
                doc._.complexity = {
                    'citations': citation_count(doc),
                    'recitals': recital_count(doc),
                    'articles': article_count(doc),
                    'structural_size': structural_size(doc, "all"),
                    'structural_size_enacting': structural_size (doc, "enacting"),
                    'references': reference_count(doc),
                    'avg_depth': avg_depth(doc, basis='element'),
                    'avg_article_depth': avg_depth (doc, basis='article'),
                    'words_noannex': word_count(doc, annex=False)
                }


            # @TODO use lambada function to call with paramters (e.g. strucutral size)


        return doc


def citation_count(doc):

    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    return(len(doc.spans['citations']))

def recital_count(doc):

    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    return(len(doc.spans['recitals']))

def count_articles():

    # @TODO: various methods for article counting (see older analysis)
    pass

def matched_articles_count(doc):
    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    return (len (doc.spans['articles']))


def last_matched_article_num(doc):
    if not doc.has_extension ("parts") or not doc.has_extension ("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc (doc)

    # @TODO (see older analysis)
    pass

def article_count(doc):
    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    # @TODO methods in older analysis
    ## using distance measures

    return(matched_articles_count(doc))


def structural_size(doc, parts = "all"):

    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    enacting_size = 0

    # loop over articles
    for article in doc._.article_elements:
        # loop over (sub)paragraphs in article
        for subpar, subparpoints, subparindents in zip(article['subpars'], article['points'], article['indents']):
            enacting_size += len(subpar)

            for indents, points in zip(subparindents, subparpoints):
                enacting_size += len(indents)
                enacting_size += len(points)

    if parts == "enacting":
        return enacting_size
    else:
        recital_size = recital_count(doc)
        return enacting_size + recital_size


def avg_depth(doc, basis = "element"):

    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    depths = {1: 0,
              2: 0,
              3: 0}

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

        for i, (subpar, subparpoints, subparindents) in enumerate(zip(article['subpars'], article['points'], article['indents'])):

            article_levels.append(par_level)

            for indents, points in zip(subparindents, subparpoints):
                indents_level = par_level + 1
                points_level = indents_level

                for indent in indents:
                    article_levels.append(indents_level)

                for point in points:
                    article_levels.append(points_level)

        articles_levels.append(article_levels)


    if basis == "article":
        # average article depth
        if len(articles_levels) == 0:
            return None
        else:
            return sum([sum(lvl)/len(lvl) for lvl in articles_levels if len(lvl) != 0])/len(articles_levels)
    elif basis == "element":
        # average element depth
        if len(articles_levels) == 0:
            return None
        else:
            return sum([sum(lvl) for lvl in articles_levels])/sum([len(l) for l in articles_levels])


def reference_count(doc):

    if not doc.has_extension("parts") or not doc.has_extension("article_elements"):
        # if function is called outside spacy pipeline

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

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

        EuplexDoc = EuplexWrapper

        doc = EuplexDoc(doc)

    word_count = sum([len(r) for r in doc.spans['recitals']]) + sum([len(c) for c in doc.spans['citations']]) + sum([len(a) for a in doc.spans['articles']])

    if annex:
        word_count += len(doc.spans['annex'])

    return word_count
