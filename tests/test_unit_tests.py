from eucy.utils import find_containing_spans
from spacy.tokens import Span
import random

def test_find_containing_spans(eudoc):

    pos_a = random.randint(100, len(eudoc.text))
    pos_b = pos_a + random.randint(1, 100)

    spans_a = find_containing_spans(eudoc, pos_a, include_article_elements=True)
    spans_ab = find_containing_spans(eudoc, pos_a, pos_b, include_article_elements=False)

    # make sure the function only returns spans or an empty list
    for spans in [spans_a, spans_ab]:
        assert isinstance(spans, list), "function does not return a list"
        assert all([isinstance(span, Span) for span in spans]) or len(spans)==0, "function does not return a list of spans or an empty list"

