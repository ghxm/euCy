"""Custom EU legal text tokenizers"""

import spacy
from spacy.tokenizer import Tokenizer
from spacy.language import Language
import re
from spacy import util

def tokenizer(nlp, name = "tokenizer", custom_exceptions = [], custom_token_match_patterns = [], overwrite_euplexcy_default = False):

    default_exceptions = nlp.Defaults.tokenizer_exceptions
    default_euplexcy_exceptions = []

    default_euplexcy_token_match_patterns = []



    # @TODO: token_match patterns need to be added as retokenization (rules)
    # @TODO: keep this for functionality reasons and add excpetions/token:mathces in a custom retokenizator?
    # otherwise normal splitting on token_match matches does not work (e.g. punctuation)

    if overwrite_euplexcy_default:
        custom_exceptions = custom_exceptions
        custom_token_match_patterns = custom_token_match_patterns
    else:
        custom_exceptions =  default_euplexcy_exceptions + custom_exceptions
        custom_token_match_patterns = default_euplexcy_token_match_patterns + custom_token_match_patterns

    custom_token_match = lambda x: [re.compile (p).match(x) for p in custom_token_match_patterns]

    return Tokenizer (nlp.vocab,
                          rules=nlp.Defaults.tokenizer_exceptions,
                          prefix_search=spacy.util.compile_prefix_regex (nlp.Defaults.prefixes).search,
                          suffix_search=spacy.util.compile_suffix_regex (nlp.Defaults.suffixes).search,
                          infix_finditer=spacy.util.compile_infix_regex (nlp.Defaults.infixes).finditer,
                          token_match=custom_token_match)



@Language.component("retokenizer")
def retokenizer(doc, name = "retokenizer", custom_retokenization_patterns = [], overwrite_euplexcy_default = False):

    euplexcy_default_patterns = [
        {'attrs': None,
         'pattern': r'\((?:[0-9]+|[a-zA-Z]{1,3})\)',
         'align': 'expand'}, # (1) (a) (EC)
        {'attrs': None,
         'pattern': r'\.{3,}',
         'align': "strict"}, # ......
        {'attrs': None,
         'pattern': r'^[0-9]+\.\s+',
         'align': "strict"}, # 1.
        {'attrs': None,
         'pattern': r'(?:(?:(?:[A-Za-z0-9])|\.{2,})+\s*/)+\s*(?:[A-Za-z0-9]+|[\.]{2,})',
         'align': "strict"},
        {'attrs': None,
         'pattern': r'\[[0-9A-Z]+\]', # footnotes
         'align': "strict"}
    ]

    if not overwrite_euplexcy_default:
        custom_retokenization_patterns = euplexcy_default_patterns + custom_retokenization_patterns

    # for regex in list of custom retokenization rules
    # create dict of match, attrs
    retok_matches = []

    for pattern in custom_retokenization_patterns:
        retok_matches.extend([{'span': m.span(), 'attrs': pattern['attrs'], 'align': pattern['align']} for m in re.finditer(pattern['pattern'], doc.text)])

    spans = []

    for match in retok_matches:
        spans.append(doc.char_span (match['span'][0], match['span'][1], alignment_mode=match['align']))

    spans = [span for span in spans if span is not None]
    spans = util.filter_spans(spans)

    with doc.retokenize () as retokenizer:
        for span in spans:
            retokenizer.merge (span)


    return doc


