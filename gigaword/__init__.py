import gzip
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
import re
from collections import namedtuple

Token = namedtuple('Token', [
    'id', 'word', 'lemma', 'begin', 'end', 'pos', 'ner'])
Sentence = namedtuple('Sentence', [
    'id', 'tokens'])
Document = namedtuple('Document', [
    'id', 'date', 'type', 'headline', 'dateline',
    'text', 'sentences', 'coreferences'])
Mention = namedtuple('Mention', [
    'representative', 'sentence', 'start', 'end', 'head'])
YMD = namedtuple('YMD', 'year month day')


def parse_ymd(text):
    year = int(text[:4])
    month = int(text[4:6])
    day = int(text[6:])
    return YMD(year, month, day)


def parse_lisp(text):
    text = text.replace('(', ' ( ')
    text = text.replace(')', ' ) ')
    text = re.sub('\\s+', ' ', text).strip()
    stack = [[]]
    for cmd in text.split(' '):
        if cmd == '(':
            stack.append([])
        elif cmd == ')':
            last = tuple(stack[-1])
            del stack[-1]
            stack[-1].append(last)
        else:
            stack[-1].append(cmd)
    return stack[0][0]


def parse_text(xml):
    p = xml.findall('P')
    if len(p) == 0:
        p = [parse_lisp(xml.text.strip())]
    else:
        p = [parse_lisp(x.text.strip()) for x in p]
    return p


def parse_mention(xml):
    return Mention(
        representative='representative' in xml.attrib,
        sentence=int(xml.find('sentence').text),
        start=int(xml.find('start').text),
        end=int(xml.find('end').text),
        head=int(xml.find('head').text))


def parse_token(xml):
    return Token(
        id=xml.attrib['id'],
        word=xml.find('word').text,
        lemma=xml.find('lemma').text,
        begin=int(xml.find('CharacterOffsetBegin').text),
        end=int(xml.find('CharacterOffsetEnd').text),
        pos=xml.find('POS').text,
        ner=xml.find('NER').text)


def parse_sentence(xml):
    return Sentence(
        id=xml.attrib['id'],
        tokens=[parse_token(x) for x in xml.find('tokens')])


def read_file(path,
              parse_headline=True, parse_dateline=True,
              parse_coreferences=True, parse_sentences=True,
              parse_text=True):
    with gzip.open(path) as source:
        source.readline()
        # file_line = source.readline() + "</FILE>"
        # file_tag = etree.fromstring(file_line)
        # file_id = file_tag.attrib['id']

        lines = []
        for line in source:
            lines.append(line)

            if line.strip() == '</DOC>':
                lines = ['<xml>'] + lines
                lines.append('</xml>')
                xml = etree.fromstringlist(lines).find('DOC')

                doc_id = xml.attrib['id']
                date_str = doc_id.split('_')[-1].split('.')[0]
                date = parse_ymd(date_str)

                headline_xml = xml.find('HEADLINE')
                if headline_xml is not None and parse_headline:
                    headline = parse_lisp(headline_xml.text.strip())
                else:
                    headline = None

                dateline_xml = xml.find('DATELINE')
                if dateline_xml is not None and parse_dateline:
                    dateline = parse_lisp(dateline_xml.text.strip())
                else:
                    dateline = None

                coreferences = xml.find('coreferences')
                if coreferences is not None and parse_coreferences:
                    coreferences = [[parse_mention(m) for m in x]
                                    for x in coreferences]
                else:
                    coreferences = []

                sentences = xml.find('sentences')
                if sentences is not None and parse_sentences:
                    sentences = [parse_sentence(x)
                                 for x in xml.find('sentences')]
                else:
                    sentences = []

                text = xml.find('TEXT')
                if text is not None and parse_text:
                    text = parse_text(text)
                else:
                    text = None

                yield Document(
                    id=xml.attrib['id'],
                    date=date,
                    type=xml.attrib['type'],
                    headline=headline,
                    dateline=dateline,
                    text=text,
                    sentences=sentences,
                    coreferences=coreferences)
                lines = []
