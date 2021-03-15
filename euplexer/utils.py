import re
from euplexer.structure import Structure, text_parts
from spacy.tokens import Doc
from spacy.tokens.span import Span


def clean_text(text, rm_fn =True):

    text = text.strip()
    text = re.sub(r'[ÕÖêöð]', '', text) # remove certain unicode characters
    text = re.sub(r'(?<=^)\s+', '', text, flags = re.MULTILINE) # remove whitespace at the beginning of a line

    text = re.sub (r'(\sof|\sin|\swith)\s*(?:[\n\r])(Article)', '\g<1> \g<2>', text)  # fix cases where there is a newline right before an Article reference (not new Article start)

    # remove lines starting with @
    text = re.sub(r'^@.*$', "", text, flags=re.MULTILINE)

    # remove footnotes
    if rm_fn:
        text = re.sub(r'^\[[0-9]+\].*', "", text, flags=re.MULTILINE)
        text = re.sub(r'^\(\).*', "", text, flags=re.MULTILINE)


    # fix spelling
    text = _fix_spaced_spelling(text, term ="Article", flags=re.IGNORECASE)
    text = _fix_spaced_spelling(text, term ="Articles", flags=re.IGNORECASE)

    return(text.strip())


def _fix_spaced_spelling(text, term, regex_pre = r'', regex_post=r'', flags = 0):

    # create the regex for the term
    regex_term_spaced = "".join([c + r"\s*" if i < len(term)-1 else c for i, c in enumerate(term)])
    regex = regex_pre + regex_term_spaced + regex_post

    return(re.sub(regex, term, text, flags=flags))


def chars_to_tokens_dict(doc, input = "as_ref", output = "as_ref"):

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
        for i in range (token.idx, token.idx + len (token.text)):
            chars_to_tokens[i-char_offset] = token.i-token_offset
    return chars_to_tokens


def char_to_token(char, reference, input = "as_ref", output = "as_ref", alignment_mode = "contract"):
    if isinstance(reference, Doc) or isinstance(reference, Span):
        char_token = chars_to_tokens_dict(reference, input = input, output = output)
    elif isinstance(reference, dict):
        char_token = reference
    else:
        raise TypeError("Argument 'reference' needs to be either a Doc, Span or a Dict object.")
    token = char_token.get (char, None)

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
            if char < min (char_token.keys ()):
                char = min (char_token.keys ())
        token = char_token.get (char, None)

    return token + token_offset



def _part_argument_check(argument, part):

    if isinstance(argument, Structure):
        return argument.parts[part]
    elif isinstance(argument, Doc):
        return text_parts(argument)[part]
    elif isinstance(argument, Span):
        return argument
    elif argument is None:
        return argument
    else:
        raise TypeError(str(type(argument)) + " type not supported. Please pass a Doc, Span or Structure object.")


def get_sentences(doclike, min_sen_length):

    if isinstance(doclike, Doc):

        return[sent for sent in doclike.sents if len(sent.text.strip()) > min_sen_length]

    elif isinstance(doclike, Span):
        # get all sentences within
       return [sent for sent in doclike.doc.sents if sent.start >= doclike.start and (sent.end<= doclike.end or sent.start <= doclike.end) if len(sent.text.strip()) > min_sen_length]
    else:
        raise ValueError("Pleanse supply a Doc or Span object.")


def get_n_tokens(n, token, direction="left"):

    if direction == "left":
        lower = token.i - n
        upper = token.i
    else:
        lower = token.i
        upper = token.i + n
    yield [tok for tok in token.doc if tok.i in  range(lower, upper)]

def get_n_left(n, token):
    return get_n_tokens(n, token, direction="left")

def get_n_right(n, token):
    return get_n_tokens(n, token, direction="right")
