import re
from spacy.tokens import Doc
from spacy.tokens.span import Span
from collections import OrderedDict
import euplexcy



def clean_text(text, rm_fn =True):

    text = text.strip()
    text = re.sub(r'[ÕÖêöð]', '', text) # remove certain unicode characters
    text = re.sub(r'(?<=^)\s+', '', text, flags = re.MULTILINE) # remove whitespace at the beginning of a line

    text = re.sub(r'\n*^((,).*)', '\g<1>', text, flags = re.MULTILINE) # put paragraphs starting with a comma back to the sentence above


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

    if isinstance(argument, euplexcy.structure.Structure):
        return argument.parts[part]
    elif isinstance(argument, Doc):
        return euplexcy.structure.text_parts(argument)[part]
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


def get_n_tokens(n, token, direction="left", ignore_ws=False, stop_at_newline = True):

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
            lower=lower - ws_count
        else:
            upper = upper + ws_count
        tok_list = [tok for tok in token.doc[lower:upper]]

    if stop_at_newline:
        newline_tok = [tok for tok in tok_list if '\n' in tok.text_with_ws]

        if len(newline_tok)>0:
            if direction == "left":
                lower = newline_tok[-1]
            else:
                upper = newline_tok[0]

    return tok_list


def get_n_left(n, token, ignore_ws=False, stop_at_newline = True):
    return get_n_tokens(n, token, direction="left", ignore_ws=ignore_ws, stop_at_newline=stop_at_newline)

def get_n_right(n, token, ignore_ws = False, stop_at_newline = True):
    return get_n_tokens(n, token, direction="right", ignore_ws=ignore_ws, stop_at_newline=stop_at_newline)


def align_span_with_text(span, text, right = True, left = False):

    if not right and not left:
        return span

    aligned_tokens = []

    search_pos_right =  0
    for i, token in enumerate(span):
        if token.is_space:
            continue
        if sum([len(t) for t in span[i:]]) >= len(text[search_pos_right:]) and i < len([t for t in span if not t.is_space]) - 4:
            tok_match = re.escape(token.text_with_ws) + "(?=" + re.escape(span[i+1].text_with_ws + span[i+2].text_with_ws) + ")" # match tri-grams
        else:
            tok_match = re.escape(token.text)
        token_in_text = re.search(tok_match, text[search_pos_right:])
        if token_in_text is not None:
            search_pos_right = token_in_text.end()
            aligned_tokens.append(token)
        else:
            if search_pos_right > 0: # if there has been a previous match
                if right:
                    break
                else:
                    aligned_tokens.append (token)
            else:
                if not left:
                    aligned_tokens.append(token)


    # + 1 for last token because spans match exclusive (until the start of the next token)
    try:
        aligned_span = span.doc[aligned_tokens[0].i:aligned_tokens[-1].i]
        return aligned_span
    except:
        return None

def letter_to_int (letter):
    letter = letter.lower().strip()
    return ord(letter)-96

def int_to_letter(num):
    return chr (96+num)


def roman_to_int(s):
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    num = 0

    for i in range (len (s) - 1):
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
