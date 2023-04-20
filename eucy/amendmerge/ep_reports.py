# Class for EP reports
# - read in the report
# - extract the text
# - method to create a full text from report
#    - under the hood checking for type, creation of table, making the merge
import re

from bs4 import BeautifulSoup


def extract_draft_resolution(text = None, include_amendments = False):

    if text is None:
        return None

    # try to restrict the text to the legisative resolution main text
    # first find the heading
    heading = re.search('^[A-Z ]+LEGISLATIVE\s*RESOLUTION', text, re.MULTILINE)

    if heading is not None:
        text = text[heading.start():]

    # then find the end of the resolution
    # -> start of next heading
    next_heading = re.search('^(?!.*(AMENDMENT|CHAPTER|SECTION|ARTICLE|PROPOSAL\s*FOR|ANNEX|RECITAL|DIRECTIVE|REGULATION))[A-Z ]{7,}', text, re.MULTILINE)

    if not include_amendments:

        if next_heading is not None:
            text = text[:next_heading.start()]

        # try to look for amendments to restrict the text even more
        # -> the beginning of the amendments
        end = re.search('(?:^Amendments\s*by\s*the\s*European\s*Parliament)|Amendment\s*1', text, re.MULTILINE)

        if end is not None:
            text = text[:end.start()]

    return text



def determine_report_type(text=None):
    """
    Determine the type of the report (taking over, table, etc.)
    :return: type of report
    """

    # @TODO i've done this before somewhere

    type = None
    subtype = None

    if text is None:
        return type

    text_draft_resolution = extract_draft_resolution(text)

    if re.search('simplified\s*procedure', text_draft_resolution, re.IGNORECASE):
        type = 'simplified_procedure'
    elif re.search('taking\s*over\s*the\s*commission\s*', text_draft_resolution, re.IGNORECASE):
        type = 'taking_over'
    elif re.search('hereinafter\s*set', text_draft_resolution, re.IGNORECASE):
        type = 'amendments'

        text_draft_resolution_amendments = extract_draft_resolution(text, include_amendments=True)

        if re.search('^s*Amendment\s*[0-9]', text_draft_resolution_amendments, re.IGNORECASE|re.MULTILINE) is not None:
            subtype = 'table'
        else:
            subtype = 'text'



    return (type, subtype)


class EpReport:

    def __init__(self, text = None, dir = None, format=None):


        self.format = format
        self.raw_text = None

        if text is not None:

            self.format = 'text'
            self.raw_text = text

        elif dir is not None:

            self.read(dir, format)

        if self.raw_text is not None:

            self.process(self.raw_text, self.format)




    def read(self, dir, format):

        if format == 'html':
            self.format = 'html'
            report_text = self.read_html(dir)

        elif format == 'doc':
            self.format = 'doc'
            report_text = self.read_doc(dir)

        elif format == 'pdf':
            self.format = 'pdf'
            report_text = self.read_pdf(dir)

        else:
            raise ValueError('report_type must be html, doc or pdf')

        return report_text

    def read_html(self, report_dir):

            with open(report_dir, 'r') as f:
                report_text = f.read()

            return report_text

    def read_doc(self, report_dir):

           pass

           # @TODO implement


    def read_pdf(self, report_dir):
            pass
            #@TODO: implement
           #         report_text = textract.process(report_dir).decode('utf-8')


    # process the text such that it can be used for a merge (create a merge table/set the type (taking over etc))
    def process(self, raw_text, format):

            if format == 'html':
                self.process_html(raw_text)

            elif format == 'doc':
                self.process_doc(raw_text)

            elif format == 'pdf':
                self.process_pdf(raw_text)

            elif format == 'text':
                self.process_text(raw_text)

            else:
                raise ValueError('format must be html, doc or pdf')


    def process_html(self, html = None):

        if html is None:
            if self.format == 'html':
                html = self.raw_text
            else:
                raise ValueError('html must be supplied as a parameter if report format is not html')

        bs = BeautifulSoup(html, 'lxml')

        # get the text
        self.text = bs.get_text()

        report_type = determine_report_type(self.text)

        self.type = report_type[0]
        self.subtype = report_type[1]

        # @TODO hier weiter: depending on type, create a merge table
        # if taking over -> empty merge table
        # if amendments -> create a merge table from the amendments
        # (leverage html structure if possible, for doc/pdf or no table,
        # maybe take a look at parltrack amendment parsing)
        # if simplified procedure / no report -> no table, set flag in object





    def process_doc(self):
        # @TODO implement
        pass

    def process_pdf(self):
        # @TODO implement
        pass

    def process_text(self):
        # @TODO implement
        pass



