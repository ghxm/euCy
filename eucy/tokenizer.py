"""Custom EU legal text tokenizers"""

import re
import warnings

import spacy
from spacy import util
from spacy.language import Language
from spacy.tokenizer import Tokenizer


def tokenizer(nlp,
              name="tokenizer",
              custom_exceptions=[],
              custom_token_match_patterns=[],
              overwrite_eucy_default=False):

    default_exceptions = nlp.Defaults.tokenizer_exceptions
    default_eucy_exceptions = []

    default_eucy_token_match_patterns = []

    # @TODO: token_match patterns need to be added as retokenization (rules)
    # @TODO: keep this for functionality reasons and add excpetions/token:mathces in a custom retokenizator?
    # otherwise normal splitting on token_match matches does not work (e.g. punctuation)

    if overwrite_eucy_default:
        custom_exceptions = custom_exceptions
        custom_token_match_patterns = custom_token_match_patterns
    else:
        custom_exceptions = default_eucy_exceptions + custom_exceptions
        custom_token_match_patterns = default_eucy_token_match_patterns + custom_token_match_patterns

    custom_token_match = lambda x: [
        re.compile(p).match(x) for p in custom_token_match_patterns
    ]

    return Tokenizer(nlp.vocab,
                     rules=nlp.Defaults.tokenizer_exceptions,
                     prefix_search=spacy.util.compile_prefix_regex(
                         nlp.Defaults.prefixes).search,
                     suffix_search=spacy.util.compile_suffix_regex(
                         nlp.Defaults.suffixes).search,
                     infix_finditer=spacy.util.compile_infix_regex(
                         nlp.Defaults.infixes).finditer,
                     token_match=custom_token_match)


@Language.component("retokenizer")
def retokenizer(doc,
                name="retokenizer",
                custom_retokenization_patterns=[],
                overwrite_eucy_default=False):

    eucy_default_patterns = [
        {
            'attrs': {
                "POS": "NUM"
            },
            'pattern': r'\((?:[0-9]+|[a-zA-Z]{1,3})\)',
            'align': 'expand'
        },  # (1) (a) (EC)
        {
            'attrs': {
                "POS": "SYM"
            },
            'pattern': r'\.{3,}',
            'align': "strict"
        },  # ......
        {
            'attrs': {
                "POS": "NUM"
            },
            'pattern': r'^[0-9]+\.\s+',
            'align': "strict"
        },  # 1.
        {
            'attrs': {
                "POS": "NUM"
            },
            'pattern': r'(?:(?:[A-Za-z0-9]|\.)+\s*/)+\s*(?:[A-Za-z0-9]|\.)+',
            'align': "strict"
        },
        {
            'attrs': {
                "POS": "X"
            },
            'pattern': r'\[[0-9A-Z]+\]',  # footnotes
            'align': "strict"
        }
    ]

    if not overwrite_eucy_default:
        custom_retokenization_patterns = eucy_default_patterns + custom_retokenization_patterns

    # for regex in list of custom retokenization rules
    # create dict of match, attrs
    retok_matches = []

    for pattern in custom_retokenization_patterns:
        retok_matches.extend([{
            'span': m.span(),
            'attrs': pattern['attrs'],
            'align': pattern['align']
        } for m in re.finditer(pattern['pattern'], doc.text)])

    spans = []

    for match in retok_matches:
        spans.append({
            'span':
            doc.char_span(match['span'][0],
                          match['span'][1],
                          alignment_mode=match['align']),
            'attrs':
            match['attrs']
        })

    spans = [span for span in spans if span['span'] is not None]
    filtered_spans = util.filter_spans([span['span'] for span in spans])
    spans = [s for s in spans if s['span'] in filtered_spans]

    with doc.retokenize() as retokenizer:
        for sp in spans:
            span = sp['span']
            attrs = sp['attrs']
            if attrs is not None:
                retokenizer.merge(span, attrs)
            else:
                retokenizer.merge(span)

    return doc
