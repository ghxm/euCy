# euCy

> [!NOTE]
> Please note that this tool is still under active development and without proper documentation. The code is not stable and the API may change in the future. Feel free to use it but be aware of the risks and contribute to the development if you can.

Tool to annotate EU legal text and compute some related measures based on spaCy.


## Installation


You can install the package from GitHub using pip:

```
pip install git+https://github.com/ghxm/euCy.git@dev
```



## Usage

> [!NOTE]
> This is a very bare bones example of how to use the package. There isn't a stable API or convenience functions yet.

```

from eucy.eucy import EuWrapper
from eucy import utils
import spacy
import urllib

nlp = spacy.blank('en')
eu_wrapper = EuWrapper(nlp)

# get html from url
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32014R1286"

# open url and get html
html = urllib.request.urlopen(url).read().decode('utf-8')

# extract text
text = utils.text_from_html(html)

# read in text
doc = eu_wrapper(text)

# print complexity stats
print(doc._.complexity)

# get list of citations
citations = doc.spans['citations']

# get list of recitals
recitals = doc.spans['recitals']

# get list of articles
articles = doc.spans['articles']

# get the article elements of the first article
ae_1 = doc._.article_elements[0]

# print the first paragraph of the first article
print(ae_1['pars'][0])


```


For a more extended overview of the usage and functionality, please see the `tests` folder in the meantime.


## Credits

This package was created with Cookiecutter_ and the `briggySmalls/cookiecutter-pypackage`_ project template.

- Cookiecutter: https://github.com/audreyr/cookiecutter
- `briggySmalls/cookiecutter-pypackage`: https://github.com/briggySmalls/cookiecutter-pypackage
