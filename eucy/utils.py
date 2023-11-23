import errno
import os
import random
import re
import signal
import warnings
from collections import OrderedDict
from functools import wraps

from bs4 import BeautifulSoup
from spacy.tokens import Doc, SpanGroup, Span
from spacy.tokens.span import Span

import eucy


def flatten_gen(l):
    for i in l:
        if isinstance(i, list):
            yield from flatten_gen(i)
        else:
            yield i


def flatten(l):
    return list(flatten_gen(l))


def _replace_text(doc, new_text, keep_ws=True, deletion_threshold=None):
    """Setter for the replacement_text extension. Should not be used directly."""

    assert isinstance(
        doc, (Doc, Span)
    ), "doc must be a Doc or Span object. Are you trying to use the _set_replacement_text() function directly?"

    if not isinstance(new_text, str):
        raise TypeError("Replacement text must be a string")

    if not keep_ws:
        return new_text

    if doc.has_extension('deleted') and doc._.deleted:
        raise ValueError("Cannot replace text in a deleted span.")

    # make sure the replacement_text extension exists
    if not doc.has_extension('replacement_text'):
        doc.set_extension('replacement_text', default=None)
        # make sure the replacement_text extension exists
    if not doc.has_extension('deleted'):
        doc.set_extension('deleted', default=False)

    # get ws at beginning and end of original text
    ws_start = re.search(r'^\s*', doc.text).group(0)
    ws_end = re.search(r'\s*$', doc.text_with_ws).group(0)

    # add ws to new text
    new_text = ws_start + new_text + ws_end

    if deletion_threshold is not None and len(new_text.strip(
    )) <= deletion_threshold:
        doc._.deleted = True

    # set replacement text
    doc._.replacement_text = new_text


def _delete_text(doc, warn_empty_group=True, keep_ws=True):
    """Setter for the deleted extension. Should not be used directly.

    Parameters
    ----------
    doc (Doc or Span):
        The doc or span object to be marked as deleted
    warn_empty_group (bool):
        If True, print a warning if the span group is empty after deletion


    """

    assert isinstance(
        doc, (Doc, Span)
    ), "doc must be a Doc or Span object. Are you trying to use the _set_deleted() function directly?"

    if not doc.has_extension('deleted'):
        doc.set_extension('deleted', default=False)
    if not doc.has_extension('replacement_text'):
        doc.set_extension('replacement_text', default=None)

    doc._.deleted = True

    if keep_ws:
        # get ws at beginning and end of original text
        ws_start = re.search(r'^\s*', doc.text).group(0)
        ws_end = re.search(r'\s*$', doc.text_with_ws).group(0)

        # set replacement text
        doc._.replacement_text = ws_start + ws_end
    else:
        doc._.replacement_text = None

    if isinstance(doc, Span):
        if warn_empty_group:

            # search for the span in the span groups
            for spangroup in doc.doc.spans:
                spangroup = doc.doc.spans[spangroup]
                if doc in list(spangroup):
                    break

                # if the span group is empty, print a warning
                if len([
                        s for s in spangroup
                        if s.has_extension('deleted') and not s._.deleted
                ]) == 0:

                    warnings.warn(
                        f'Span group "{ spangroup.name }" will be empty after deletion of element'
                    )



def _auto_position(position, element_list_length, return_int=False):
    if isinstance(position, int):
        if position < element_list_length / 2:
            if return_int:
                return 0
            return 'start'
        else:
            if return_int:
                return element_list_length
            return 'end'
    elif isinstance(position, str) and position in ['start', 'end']:
        if position == 'start':
            if return_int:
                return 0
            return 'start'
        else:
            if return_int:
                return element_list_length
            return 'end'

    raise ValueError("position must be an integer or 'start' or 'end'")

def _new_element_span(doc, new_text, add_ws = True):
    # check if doc is a doc or span object
    assert isinstance(doc, (Doc)), "doc must be a Doc object"

    # check if new text is a string
    assert isinstance(new_text, (str, Span)), "New text must be a string or a Span object"

    # prepare new span
    # make sure the add_text extension exists
    if isinstance(new_text, Span):
        if not new_text.has_extension('new_element'):
            Span.set_extension('new_element', default=False)
        if not new_text.has_extension('char_pos'):
            Span.set_extension('char_pos', default=None)

    if isinstance(new_text, str):

        new_span = None

        # create a random span that is not equal to any existing span
        while new_span is None or (new_span.has_extension('replacement_text') and new_span._.replacement_text is not None):

            # choose a random start and end char pos
            start = random.randint(0, len(doc.text)-1)
            end = start+1

            new_span = doc.char_span(start, end, alignment_mode='expand')

            # check to make sure we're not overlapping with an existing span
            existing_spans = find_containing_spans(doc, new_span.start_char, new_span.end_char, include_article_elements=True)

            if len(existing_spans) > 0:
                new_span = None

        set_extensions(new_span)
        new_span._.replacement_text = new_text
    else:
        new_span = new_text
        if new_span._.replacement_text is None:
            new_span._.replacement_text = new_span.text
        new_text = new_span.text_with_ws

    if add_ws:
        new_span._.replacement_text = '\n\n' + new_text + '\n\n'

    # set new element flag
    new_span._.new_element = True

    return new_span

def _add_article_element(doc,
                         new_text,
                         article,
                         paragraph=None,
                         subparagraph=None,
                         indent=None,
                         point=None,
                         auto_position = True,
                         add_ws=True):
    """Setter for the add_element extension. Should not be used directly."""

    assert isinstance(article, int), "article must be an integer"
    assert any([paragraph is not None, subparagraph is not None, indent is not None, point is not None]), "at least one of paragraph, subparagraph, indent or point must be specified"

    article_elements = doc._.article_elements[article]

    #if subparagraph and not paragraph:
    #    raise ValueError("paragraph must be specified if subparagraph is specified")

    if paragraph and not ((isinstance(paragraph, int) and paragraph in range(len(article_elements['pars']))) or paragraph in ['start', 'end']):
        if auto_position and isinstance(paragraph, int):
            paragraph = _auto_position(paragraph, len(article_elements['pars']), return_int=True)
        else:
            raise ValueError("paragraph must be an integer inside the range of the paragraph list")
    elif paragraph and paragraph in ['start', 'end']:
        paragraph = _auto_position(paragraph, len(article_elements['pars']), return_int=True)

    if subparagraph and not ((isinstance(subparagraph, int) and subparagraph in range(len(article_elements['subpars'][paragraph]))) or subparagraph in ['start', 'end']):
        if auto_position and isinstance(subparagraph, int):
            subparagraph = _auto_position(subparagraph, len(article_elements['subpars'][paragraph]), return_int=True)
        else:
            raise ValueError("subparagraph must be an integer inside the range of the subparagraph list")
    elif subparagraph and subparagraph in ['start', 'end']:
        subparagraph = _auto_position(subparagraph, len(article_elements['subpars'][paragraph]), return_int=True)

    if indent and not ((isinstance(indent, int) and indent in range(len(article_elements['indents'][paragraph][subparagraph]))) or indent in ['start', 'end']):
        if auto_position and isinstance(indent, int):
            indent = _auto_position(indent, len(article_elements['indents'][paragraph][subparagraph]), return_int=True)
        else:
            raise ValueError("indent must be an integer inside the range of the indent list")
    elif indent and indent in ['start', 'end']:
        indent = _auto_position(indent, len(article_elements['indents'][paragraph][subparagraph]), return_int=True)

    if point and not ((isinstance(point, int) and point in range(len(article_elements['points'][paragraph][subparagraph]))) or point in ['start', 'end']):
        if auto_position and isinstance(point, int):
            point = _auto_position(point, len(article_elements['points'][paragraph][subparagraph]), return_int=True)
        else:
            raise ValueError("point must be an integer inside the range of the point list")
    elif point and point in ['start', 'end']:
        point = _auto_position(point, len(article_elements['points'][paragraph][subparagraph]), return_int=True)

    new_span = _new_element_span(doc, new_text, add_ws=add_ws)
    set_element_extensions(new_span)

    # if no further information is given, we're in the first (sub)paragraph
    if paragraph is None:
        paragraph = 0

    #if subparagraph is None:
    #    subparagraph = 1

    # start processing from the most nested element
    article_element_type = None
    article_elements_spans = None

    spans_without_new_elements = lambda x: [
        s for s in x if not s._.new_element
    ]

    # TODO handle cases where point AND indent are specified?
    # determine char_pos of new element
    if point is not None:
        position = point
        article_element_type = 'points'
        article_elements_spans = article_elements['points'][paragraph][subparagraph]
    elif indent is not None:
        position = indent
        article_element_type = 'indents'
        article_elements_spans = article_elements['indents'][paragraph][subparagraph]
    elif subparagraph is not None:
        position = subparagraph
        article_element_type = 'subpars'
        article_elements_spans = article_elements['subpars'][paragraph]
    elif paragraph is not None:
        position = paragraph
        article_element_type = 'pars'
        article_elements_spans = article_elements['pars']

    if article_element_type in ['indents', 'points'] and  len(spans_without_new_elements(article_elements_spans)) == 0:
            # case where no pre-existing elements of the same type exist
            ## use subparagraph end char pos
            new_span._.char_pos = spans_without_new_elements(article_elements['subpars'][article])[subparagraph-1].end_char
    else:
        if position in range(len(spans_without_new_elements(article_elements_spans))):
            ## insert at position
            new_span._.char_pos = spans_without_new_elements(article_elements_spans)[position].start_char
        else:
            ## insert at end
            new_span._.char_pos = spans_without_new_elements(article_elements_spans)[-1].end_char

    new_span._.element_type = 'art_' + article_element_type[:-1]

    # insert into span group at position in a bit of a hacky way
    new_article_elements_spans = [
        e for i, e in enumerate(article_elements_spans) if i < position
    ] + [new_span] + [
        e for i, e in enumerate(article_elements_spans) if i >= position
    ]

    if article_element_type == 'points':
        article_elements['points'][paragraph][subparagraph] = new_article_elements_spans
    elif article_element_type == 'indents':
        article_elements['indents'][paragraph][subparagraph] = new_article_elements_spans
    elif article_element_type == 'subpars':
        article_elements['subpars'][paragraph] = new_article_elements_spans
    elif article_element_type == 'pars':
        article_elements['pars'] = new_article_elements_spans

    # re-assign article elements
    doc._.article_elements[article] = article_elements












def _add_element(doc,
                 new_text,
                 element_type=None,
                 position='end',
                 auto_position=True,
                 add_ws=True):
    """Setter for the add_element extension. Should not be used directly."""

    assert element_type in [
        'citation', 'recital', 'article'
    ], "element_type must be one of 'citations', 'recitals', 'articles'"

    if not(position in ['end', 'start'] or (
            isinstance(position, int) and
            (position in range(len(doc.spans[element_type + 's'])))
            or position == 0)
        ):
        if auto_position and isinstance(position, int):
                # determine whether to insert at start or end of span group
            position = _auto_position(position, len(doc.spans[element_type + 's']), return_int=True)
        else:
            raise AssertionError("position must be one of 'end', 'start' or an integer inside the range of the span group")
    elif position in ['end', 'start']:
        position = _auto_position(position, len(doc.spans[element_type + 's']), return_int=True)

    if position > len(doc.spans[element_type + 's']):
        position = len(doc.spans[element_type + 's'])

    new_span = _new_element_span(doc, new_text, add_ws=add_ws)

    spangroup_name = element_type + 's'

    sg_without_new_elements = lambda x: [
        s for s in doc.spans[x] if not s._.new_element
    ]

    # add the char pos (pos where the element is inserted, needed for text recreation in modify.modify_text)

    if len(sg_without_new_elements(spangroup_name)) == 0:

        # if the span group is empty (no elments of the added type)

        warnings.warn(
            f'Span group "{ element_type }" is empty. The new element will be inserted at an approximate position but is likely to be incorrect.'
        )

        if element_type == 'recital':
            ## use citation end char pos
            try:
                new_span._.char_pos = sg_without_new_elements(
                    'citations')[-1].end_char
            except:
                new_span._.char_pos = sg_without_new_elements(
                    'articles')[0].start_char

        elif element_type == 'citation':

            ## use recital end char pos
            try:
                new_span._.char_pos = sg_without_new_elements(
                    'rectials')[0].start_char
            except:
                new_span._.char_pos = sg_without_new_elements(
                    'articles')[0].start_char

        else:

            raise ValueError(
                'Cannot insert article in document without articles')

    else:
        if position in range(len(sg_without_new_elements(spangroup_name))):
            ## insert at position
            new_span._.char_pos = sg_without_new_elements(
                spangroup_name)[position].start_char

        else:
            ## insert at end
            new_span._.char_pos = sg_without_new_elements(
                spangroup_name)[-1].end_char

    # insert into span group at position in a bit of a hacky way
    doc.spans[spangroup_name] = [
        e for i, e in enumerate(doc.spans[spangroup_name]) if i < position
    ] + [new_span] + [
        e for i, e in enumerate(doc.spans[spangroup_name]) if i >= position
    ]

    #return doc


_extensions = {
    "Doc": [
        {
            'name': 'article_elements',
            'default': None
        },
        {
            'name': 'parts',
            'default': None
        },
        {
            'name': 'title',
            'default': None
        },
        {
            'name': 'readability',
            'default': None
        },
        {
            'name': 'complexity',
            'default': None
        },
        {
            'name': 'no_text',
            'default': None
        },
        {
            'name': 'deleted',
            'default': False
        },
        {
            'name': 'delete_text',
            'method': _delete_text
        },
        {
            'name': 'delete',  # alias for delete_text
            'method': _delete_text
        },
        {
            'name': 'replacement_text',
            'default': None
        },
        {
            'name': 'replace_text',
            'method': _replace_text,
        },
        {
            'name': 'replace',  # alias for replace_text
            'method': _replace_text,
        },
        {
            'name': 'add_element',
            'method': _add_element
        },
        {
            'name': 'add_article_element',
            'method': _add_article_element
        }
    ],
    "Span": [
        {
            'name': 'deleted',
            'default': False
        },
        {
            'name': 'delete_text',
            'method': _delete_text
        },
        {
            'name': 'delete',  # alias for delete_text
            'method': _delete_text
        },
        {
            'name': 'replacement_text',
            'default': None
        },
        {
            'name': 'replace_text',
            'method': _replace_text,
        },
        {
            'name': 'replace',  # alias for replace_text
            'method': _replace_text,
        },
        {
            'name': 'new_element',
            'default': False
        },
        {
            'name': 'char_pos',
            'default': None
        },
        {
            'name': 'new_start_char',
            'default': None
        },
        {
            'name': 'new_end_char',
            'default': None
        }
    ]
}


def set_extensions(doc=None, force=False):
    """Set all Doc and Span extensions required by euCy."""

    if isinstance(doc, Doc):

        for extension in _extensions['Doc']:
            try:
                doc.set_extension(**extension, force=force)
            except ValueError:
                pass

        return None

    elif isinstance(doc, Span):

        for extension in _extensions['Span']:
            try:
                doc.set_extension(**extension, force=force)
            except ValueError:
                pass

        return None

    elif doc is None:

        for extension in _extensions['Doc']:
            try:
                Doc.set_extension(**extension, force=force)
            except ValueError:
                pass

        for extension in _extensions['Span']:
            try:
                Span.set_extension(**extension, force=force)
            except ValueError:
                pass

        return None

    else:

        raise TypeError("doc must be a Doc or Span object")


def text_from_html(html):
    """Extract text from html"""

    if isinstance(html, BeautifulSoup):
        soup = html
    else:
        soup = BeautifulSoup(html, 'lxml')

    text = soup.get_text(separator="\n\n", strip=True)

    text = re.sub(r'(?<!\n)\n{1}(?!\n)', "", text, flags=re.MULTILINE)

    return text


def clean_text(text, rm_fn=True):

    text = text.strip()
    text = re.sub(r"""[
ÕÖêöð]""", '', text)  # remove certain unicode characters
    text = re.sub(
        r'(?<=^)\s+', '', text,
        flags=re.MULTILINE)  # remove whitespace at the beginning of a line

    text = re.sub(
        r'\n*^((,).*)', '\g<1>', text, flags=re.MULTILINE
    )  # put paragraphs starting with a comma back to the sentence above

    text = re.sub(
        r'(\sof|\sin|\swith)\s*(?:[\n\r])(Article)', '\g<1> \g<2>', text
    )  # fix cases where there is a newline right before an Article reference (not new Article start)

    # remove lines starting with @
    text = re.sub(r'^@.*$', "", text, flags=re.MULTILINE)

    # remove footnotes
    if rm_fn:
        text = re.sub(r'^\[[0-9]+\].*', "", text, flags=re.MULTILINE)
        text = re.sub(r'^\(\).*', "", text, flags=re.MULTILINE)

    # fix spelling
    text = _fix_spaced_spelling(text, term="Article", flags=re.IGNORECASE)
    text = _fix_spaced_spelling(text, term="Articles", flags=re.IGNORECASE)

    return text.strip()


def _fix_spaced_spelling(text, term, regex_pre=r'', regex_post=r'', flags=0):

    # create the regex for the term
    regex_term_spaced = "".join(
        [c + r"\s*" if i < len(term) - 1 else c for i, c in enumerate(term)])
    regex = regex_pre + regex_term_spaced + regex_post

    return (re.sub(regex, term, text, flags=flags))


def chars_to_tokens_dict(doc, input="as_ref", output="as_ref"):

    # Helper function to create lookup dict to match text char positions to token numbers
    # see https://github.com/explosion/spaCy/issues/4158#issuecomment-523400114

    chars_to_tokens = {}

    if isinstance(doc, Span) and input == "doc":
        doc = doc.doc
        char_offset = 0
    elif isinstance(doc, Span) and input == "as_ref":
        input = "span"
        char_offset = doc.start_char
    else:
        input = "doc"
        char_offset = 0

    if output == "as_ref":
        output = input

    if output == "span":
        token_offset = doc.start
    else:
        token_offset = 0

    for token in doc:
        for i in range(token.idx, token.idx + len(token.text)):
            chars_to_tokens[i - char_offset] = token.i - token_offset
    return chars_to_tokens


def char_to_token(char,
                  reference,
                  input="as_ref",
                  output="as_ref",
                  alignment_mode="contract"):
    if isinstance(reference, Doc) or isinstance(reference, Span):
        char_token = chars_to_tokens_dict(reference,
                                          input=input,
                                          output=output)
    elif isinstance(reference, dict):
        char_token = reference
    else:
        raise TypeError(
            "Argument 'reference' needs to be either a Doc, Span or a Dict object."
        )
    token = char_token.get(char, None)

    token_offset = 0

    while token is None:
        if alignment_mode == "expand":
            char = char + 1
            if char > max(char_token.keys()):
                char = max(char_token.keys())
                token_offset = 1
        elif alignment_mode == "strict":
            return None
        else:
            char = char - 1
            if char < min(char_token.keys()):
                char = min(char_token.keys())
        token = char_token.get(char, None)

    return token + token_offset


def _part_argument_check(argument, part):

    if isinstance(argument, eucy.structure.Structure):
        return argument.parts[part]
    elif isinstance(argument, Doc):
        return eucy.structure.text_parts(argument)[part]
    elif isinstance(argument, Span):
        return argument
    elif argument is None:
        return argument
    else:
        raise TypeError(
            str(type(argument)) +
            " type not supported. Please pass a Doc, Span or Structure object."
        )


def get_sentences(doclike, min_sen_length):

    if isinstance(doclike, Doc):

        return [
            sent for sent in doclike.sents
            if len(sent.text.strip()) > min_sen_length
        ]

    elif isinstance(doclike, Span):
        # get all sentences within
        return [
            sent for sent in doclike.doc.sents
            if sent.start >= doclike.start and (
                sent.end <= doclike.end or sent.start <= doclike.end)
            if len(sent.text.strip()) > min_sen_length
        ]
    else:
        raise ValueError("Pleanse supply a Doc or Span object.")


def get_n_tokens(n,
                 token,
                 direction="left",
                 ignore_ws=False,
                 stop_at_newline=True):

    if direction == "left":
        lower = token.i - n
        upper = token.i
    else:
        lower = token.i
        upper = token.i + n
    tok_list = [tok for tok in token.doc[lower:upper]]
    if ignore_ws:
        ws_count = len([t for t in tok_list if t.is_space])
        if direction == "left":
            lower = lower - ws_count
        else:
            upper = upper + ws_count
        tok_list = [tok for tok in token.doc[lower:upper]]

    if stop_at_newline:
        newline_tok = [tok for tok in tok_list if '\n' in tok.text_with_ws]

        if len(newline_tok) > 0:
            if direction == "left":
                lower = newline_tok[-1]
            else:
                upper = newline_tok[0]

    return tok_list


def get_n_left(n, token, ignore_ws=False, stop_at_newline=True):
    return get_n_tokens(n,
                        token,
                        direction="left",
                        ignore_ws=ignore_ws,
                        stop_at_newline=stop_at_newline)


def get_n_right(n, token, ignore_ws=False, stop_at_newline=True):
    return get_n_tokens(n,
                        token,
                        direction="right",
                        ignore_ws=ignore_ws,
                        stop_at_newline=stop_at_newline)


def align_span_with_text(span, text, right=True, left=False):

    if not right and not left:
        return span

    aligned_tokens = []

    search_pos_right = 0
    for i, token in enumerate(span):
        if token.is_space:
            continue
        if sum([len(t) for t in span[i:]]) >= len(
                text[search_pos_right:]) and i < len(
                    [t for t in span if not t.is_space]) - 4:
            tok_match = re.escape(token.text_with_ws) + "(?=" + re.escape(
                span[i + 1].text_with_ws +
                span[i + 2].text_with_ws) + ")"  # match tri-grams
        else:
            tok_match = re.escape(token.text)
        token_in_text = re.search(tok_match, text[search_pos_right:])
        if token_in_text is not None:
            search_pos_right = token_in_text.end()
            aligned_tokens.append(token)
        else:
            if search_pos_right > 0:  # if there has been a previous match
                if right:
                    break
                else:
                    aligned_tokens.append(token)
            else:
                if not left:
                    aligned_tokens.append(token)

    # + 1 for last token because spans match exclusive (until the start of the next token)
    try:
        aligned_span = span.doc[aligned_tokens[0].i:aligned_tokens[-1].i]
        return aligned_span
    except:
        return None


def letter_to_int(letter):
    letter = letter.lower().strip()
    return ord(letter) - 96


def int_to_letter(num):
    return chr(96 + num)


def roman_to_int(s):
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    num = 0

    for i in range(len(s) - 1):
        if roman[s[i]] < roman[s[i + 1]]:
            num += roman[s[i]] * -1
            continue

        num += roman[s[i]]

    num += roman[s[-1]]

    return num


def int_to_roman(num):

    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):

    def decorator(func):

        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL,
                             seconds)  #used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


def element_list_to_spans(element_list,
                          level=0,
                          element_type=None,
                          article_num=None):
    """Recursive function to loop through element lists and annotate the span by article number and element type, num and level"""

    return_list = []

    for i, element in enumerate(element_list, 1):
        if isinstance(element, list):
            element_list_to_spans(element,
                                  level=level + 1,
                                  element_type=element_type,
                                  article_num=article_num)
        else:
            element._.article = article_num
            element._.type = element_type
            element._.num = i
            element._.level = level

            return_list.append(element)

    return return_list


def article_elements_to_spangroup(doc):
    """Converts ._.article_elements from to a SpanGroup (doc.spans['article_elements']) and adds the type, num, level attributes as extensions"""

    # @TODO alternative: add elements as extension to articles span group

    # create span group for article elements
    doc.spans['article_elements'] = SpanGroup(doc)

    # set span level attributes
    Span.set_extension('article', default=None, force=True)
    Span.set_extension('type', default=None, force=True)
    Span.set_extension('level', default=None, force=True)
    Span.set_extension('num', default=None, force=True)

    # get all article elements
    article_elements = [span for span in doc._.article_elements]

    for art_num, article_elements in enumerate(article_elements, 1):

        for element_type, elements in article_elements.items():

            doc.spans['article_elements'].extend(
                element_list_to_spans(elements,
                                      element_type=element_type[:-1],
                                      article_num=art_num))

    return doc


def get_element_by_match(doc, match_text, method='exact'):
    """Returns the element span of the given match text"""

    # @TODO

    raise NotImplementedError


def get_element_by_num(doc,
                       citation=None,
                       recital=None,
                       article=None,
                       par=None,
                       subpar=None,
                       point=None,
                       indent=None):
    """Returns the span of the given element"""

    # make sure all elements are either None or int
    assert all([
        isinstance(x, int) or x is None
        for x in [citation, recital, article, par, subpar, point, indent]
    ]), "All element arguments must be either None or int"

    # make sure article elements specify the required level correctly
    assert not any([
        par, subpar, point, indent
    ]) and article is None, "Article elements must specify article number"

    assert not any([
        subpar, point, indent
    ]) and par is None, "Paragraph elements must specify paragraph number"

    if par is not None and subpar is None:
        subpar = 1

    # reduce all int arguments by one to match the list index
    citation = citation - 1 if citation is not None else None
    recital = recital - 1 if recital is not None else None
    article = article - 1 if article is not None else None
    par = par - 1 if par is not None else None
    subpar = subpar - 1 if subpar is not None else None
    point = point - 1 if point is not None else None
    indent = indent - 1 if indent is not None else None

    if citation is not None:
        return doc.spans['citations'][citation]
    elif recital is not None:
        return doc.spans['recitals'][recital]
    elif article is not None and not any([par, subpar, point, indent]):
        return doc.spans['articles'][article]
    elif article is not None and any([par, subpar, point, indent]):
        if indent is not None:
            return doc.spans['article_elements'][article].get(
                'indents')[par][subpar][indent]
        elif point is not None:
            return doc.spans['article_elements'][article].get(
                'points')[par][subpar][point]
        elif subpar is not None:
            return doc.spans['article_elements'][article].get(
                'subpars')[par][subpar]
        elif par is not None:
            return doc.spans['article_elements'][article].get('pars')[par]
    else:
        raise ValueError("No element specified")


def get_element_text(element, replace_text=False):
    """Returns the text of the given element

    Parameters
    ----------
    element (Span): The element to get the text from
    replace_text (bool): If True, returns the replacement text (if not None), otherwise returns the original text


    Returns
    -------
    text (str): The text of the element


    """

    assert isinstance(element,
                      (Span, Doc)), "element must be a Span/Doc object"

    if replace_text and element.has_extension(
            'replacement_text') and element._.replacement_text is not None:
        text = element._.replacement_text
    else:
        text = element.text

    return text


def element_text_to_markup(text,
                           element_type=None,
                           element_num=None,
                           keep_open=False,
                           **kwargs):
    """Converts the given text to markup using the given element type and number

    Parameters:
    text (str): The text to convert to markup
    element_type (str): The element type to use for the markup
    element_num (int): The element number to use for the markup
    keep_open (bool): Whether to keep the element open (i.e. not add the closing tag)
    kwargs (dict): Additional attributes to add to the element

    Returns:
    markup (str): The markup of the text

    """

    quote = "'"

    if element_type is None:
        return text
    else:
        return f"<{element_type}{' ' if element_num is not None else ''}{f'num={quote}{element_num}{quote}' if element_num is not None else ''}{' ' if kwargs else ''}{' '.join([f'{k}={quote}{v}{quote}' for k, v in kwargs.items()])}{'' if keep_open else ''}>" + text + (
            f"</{element_type}>" if not keep_open else "")


def element_to_markup(element,
                      element_type=None,
                      element_num=None,
                      replace_text=False,
                      keep_open=False,
                      **kwargs):
    """Converts the given element to markup using the given element type and number

    Parameters:
    element (Span): The element to convert to markup
    element_type (str): The element type to use for the markup
    element_num (int): The element number to use for the markup
    replace_text (bool): Whether to use the replacement text instead of the original text
    keep_open (bool): Whether to keep the element open (i.e. not add the closing tag)
    kwargs (dict): Additional attributes to add to the element

    Returns:
    markup (str): The markup of the element

    """

    element_text = get_element_text(element, replace_text=replace_text)

    return element_text_to_markup(element_text,
                                  element_type=element_type,
                                  element_num=element_num,
                                  keep_open=keep_open,
                                  **kwargs)


def elements_to_text(doc,
                     element_markup=True,
                     replace_text=True,
                     article_elements=True):
    """Re-builds the text of the law from the detected elements and returns the text

    Parameters:
    doc (Doc): The doc object to rebuild the text from
    element_markup (bool): If True, the elements will be annotated in the text using element markup (useful if re-reading the text into a euCy doc object)
    replace_text (bool): If True, the element text will be replaced with the text from the ._.replacement_text attribute
    article_elements (bool): If True, the article elements will be considered to create the text (otherwise the full article text will be used)

    Returns:
    text (str): The rebuilt text

    """

    # @TODO add option to set order of recitals/citations (set flag in eudoc?)
    #     -> check span starts
    # @TODO add (optional) marginal text (like 'whereas', 'have decided as follows', 'done at', etc.)
    #     -> anything outside the span range of the articles, recitals, citations, etc. is considered marginal text

    assert isinstance(doc, Doc), "doc must be a Doc object"
    assert doc.spans.get(
        'articles') is not None, "doc must have the articles span"
    assert doc.spans.get(
        'citations') is not None, "doc must have the citations span"
    assert doc.spans.get(
        'recitals') is not None, "doc must have the recitals span"

    if article_elements:
        assert doc.has_extension(
            'article_elements'), "doc must have the article_elements extension"
        doc = article_elements_to_spangroup(doc)

    text = ''

    # PREAMBLE
    text += '\n\n<preamble>\n\n' if element_markup else '\n\n'

    # @TODO add distinction between numbered and unnumbered recitals

    preamble_order = ['citations', 'recitals']

    # check if recitals or citations come first
    if doc.spans['recitals'][0].start < doc.spans['citations'][0].start:
        preamble_order.reverse()

    for element_type in preamble_order:

        text += '\n'

        for e_i, element in enumerate(doc.spans[element_type], 1):
            text += '\n'
            text += element_to_markup(
                element,
                element_type=element_type[:-1],
                element_num=e_i,
                replace_text=replace_text
            ) if element_markup else get_element_text(
                element, replace_text=replace_text) + '\n'
            text += '\n'

        text += '\n'

    text += '\n\n</preamble>\n\n' if element_markup else '\n\n'

    # get articles
    text += '\n\n<enactingTerms>\n\n' if element_markup else '\n\n'

    if not article_elements:
        for a_i, article in enumerate(doc.spans['articles'], 1):
            text += element_to_markup(
                article,
                element_type='article',
                element_num=a_i,
                replace_text=replace_text
            ) if element_markup else get_element_text(
                article, replace_text=replace_text) + '\n'
    else:

        for a_i, article in enumerate(doc._.article_elements, 1):
            # paragraph
            # @TODO add distinction between numbered and unnumbered paragraphs

            text += '\n'

            text += f"\n<article num='{a_i}'>\n" if element_markup else f"Article {a_i}.\n\n"

            for p_i, par in enumerate(article.get('pars', []), 1):

                text += element_to_markup(
                    par,
                    element_type='paragraph',
                    element_num=p_i,
                    replace_text=replace_text,
                    keep_open=True) if element_markup else get_element_text(
                        par, replace_text=replace_text) + '\n'

                # get list of sub-paragraph elements from the spangroups
                subpar_elements = [
                    e
                    for e in doc.spans.get('article_elemenets', SpanGroup(doc))
                    if e._.get('type') in ['subpar', 'indent', 'point']
                ]

                # filter out elements that are not in the current paragraph
                subpar_elements = [
                    e for e in subpar_elements
                    if e.start >= par.start and e.end <= par.end
                ]

                # sort the elements by start position
                subpar_elements = sorted(subpar_elements,
                                         key=lambda e: e.start)

                subpar_open = False

                # check if there are any sub-paragraph elements
                for subpar_element in subpar_elements:

                    if subpar_element._.get('type', '') == 'subpar':
                        # Open sub-paragraph and add the element
                        element_to_markup(
                            subpar_element,
                            element_type='subpar',
                            element_num=subpar_element._.get('num'),
                            replace_text=replace_text,
                            keep_open=True
                        ) if element_markup else get_element_text(
                            subpar_element, replace_text=replace_text) + '\n'
                        subpar_open = True
                        open_subpar_span = subpar_element
                    elif subpar_element._.get('type',
                                              '') in ['indent', 'point']:

                        if subpar_open:
                            # check if element outside subpar
                            if subpar_element.start > open_subpar_span.end:
                                # close subpar
                                text += '\n</subpar>\n' if element_markup else '\n'
                                subpar_open = False

                        # add indent
                        element_to_markup(
                            subpar_element,
                            element_type=subpar_element._.get('type', ''),
                            element_num=subpar_element._.get('num'),
                            replace_text=replace_text,
                            keep_open=False
                        ) if element_markup else get_element_text(
                            subpar_element, replace_text=replace_text) + '\n'

                # close subpar if still open
                if subpar_open:
                    text += '\n</subpar>\n' if element_markup else '\n'
                    subpar_open = False

                text += '\n</paragraph>\n' if element_markup else '\n'

            text += '\n</article>\n' if element_markup else '\n\n'

    text += '\n\n</enactingTerms>\n\n' if element_markup else '\n\n'

    return text


def is_eucy_doc(doc):
    """Checks if the given doc object is a euCy doc object"""

    return isinstance(doc, Doc) and doc.has_extension(
        'article_elements') and doc.has_extension('parts')


def find_containing_spans(doc, pos_a, pos_b = None, include_article_elements = False):
    """Returns a list of spans that contain the given position


    Parameters
    ----------
    doc (Doc): The doc object to check
    pos_a (int): The (start) char position to check
    pos_b (int): The end char position to check (optional)

    Returns
    -------
    containing_spans (list): A list of spans that contain the given position ordered by span length (ascending)
    """

    if pos_b:
        assert pos_a <= pos_b, "pos_a must be smaller than or equal to pos_b"

    spans_to_check = []
    containing_spans = []


    # get a list of spangroups
    spangroups = [sg for sg in doc.spans.keys()]

    if include_article_elements:
        # add article elements to spangroups
        article_elements = doc._.article_elements if doc.has_extension('article_elements') else []

        for article in article_elements:
            for paragraph in article['pars']:
                spans_to_check.append(paragraph)

    # check all spangroups for spans that contain the given position

    for spangroup in spangroups:
        for gspan in doc.spans[spangroup]:
            spans_to_check.append(gspan)

    for span in spans_to_check:
        if pos_b:
            if span.start_char <= pos_a and span.end_char >= pos_b:
                containing_spans.append(span)
        else:
            if span.start_char <= pos_a and span.end_char >= pos_a:
                containing_spans.append(span)

    # order by smallest span first
    containing_spans = sorted(containing_spans, key=lambda x: len(x.text))

    return containing_spans


def determine_span_group_order(doc):
    """Return the order of the span groups (citations, recitals, articles) in the given doc object"""

    sg_labels = ['citations', 'recitals', 'articles']

    # if span group is empty, remove it from the list
    sg_labels = [sg for sg in sg_labels if len(doc.spans[sg]) > 0]

    # order labels by span group start position
    sg_labels = sorted(sg_labels, key=lambda x: doc.spans[x][0].start)

    return sg_labels


def is_modified_span(span):
    """Checks if the given span has been modified"""

    assert isinstance(span, Span), "span must be a Span object"

    return (span.has_extension('deleted') and span._.deleted) or (span.has_extension('new_element') and span._.new_element) or (span.has_extension('replacement_text') and span._.replacement_text is not None)

def any_modified_spans(span_list):
    return any([is_modified_span(span) for span in span_list])


def set_element_extensions(span):
    """Set element extensions for a span
    """

    assert isinstance(span, Span), "span must be a spacy Span object"

    if not span.has_extension("element_type"):
        span.set_extension("element_type", default=None)

    if not span.has_extension("element_pos"):
        span.set_extension("element_pos", default=None)

    if not span.has_extension("element_num"):
        span.set_extension("element_num", default=None)

    if not span.has_extension("element_numstr"):
        span.set_extension("element_numstr", default=None)
