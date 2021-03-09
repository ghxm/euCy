"""Main module."""

import spacy
from spacy.tokens import Doc, Span
from euplexer import structure
from euplexer import elements
from euplexer import content
from euplexer import exceptions

class EuplexWrapper:

    # Spacy pipeline component
    # (Parts called here can also be used inidividually and without the pipeline functonality)
    # but thsi si a wrapepr for them

    # EUPLEX version of a Spacy Doc obbjects that extends it by
    # a structure attribute/funciton (that stores infromation that calls resp spacy tokennts e/attributes)
    # a complexity attribute that provides statistics on the computed values from various package functions
    # (by supplying an EuplexDoc obbject to a pakage function, it can use the additional information to make better inference)
    # class to run all analyses on a
    # returnns a combination of a spacy object and some additional information

    def __init__(self):

        if not Doc.has_extension("parts"):
            self.EuplexStructure = structure.Structure()
        if not Doc.has_extension("article_elements"):
            self.EuplexElements = elements.Elements()

        # Register extensions
        if not Doc.has_extension("complexity"):
            Doc.set_extension("complexity", default = None)

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
            if doc._.complexity is None:
                doc._.complexity = {
                    'citations': citation_count(doc),
                    'recital_count': recital_count(doc),

                }


            # Get complexity measures
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

    return(len(doc.spans['articles']))


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
        return sum([sum(lvl)/len(lvl) for lvl in articles_levels])/len(articles_levels)
    elif basis == "element":
        # average element depth
        return sum([sum(lvl) for lvl in articles_levels])/sum([len(l) for l in articles_levels])





    if parts == "enacting":
        return enacting_size
    else:
        recital_size = recital_count(doc)
        return enacting_size + recital_size

