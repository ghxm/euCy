from eucy.utils import find_containing_spans
from spacy.tokens import Span
import random

def test_find_containing_spans(eudoc):

    spans = find_containing_spans(eudoc, random.randint(100, len(eudoc.text)), include_article_elements=True)

    # make sure the function only returns spans or an empty list
    assert isinstance(spans, list), "function does not return a list"
    assert all([isinstance(span, Span) for span in spans]) or len(spans)==0, "function does not return a list of spans or an empty list"
