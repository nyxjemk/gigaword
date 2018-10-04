import gzip
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
import re
from collections import namedtuple

Token = namedtuple('Token', [
    'id', 'word', 'lemma', 'begin', 'end', 'pos', 'ner'])
SToken = namedtuple('SToken', [
    'id', 'word'])
Sentence = namedtuple('Sentence', [
    'id', 'tokens'])
Document = namedtuple('Document', [
    'id', 'date', 'type', 'headline', 'dateline',
    'text', 'sentences', 'coreferences'])
Mention = namedtuple('Mention', [
    'representative', 'sentence', 'start', 'end', 'head'])
YMD = namedtuple('YMD', 'year month day')


def _parse_ymd(text):
    year = int(text[:4])
    month = int(text[4:6])
    day = int(text[6:])
    return YMD(year, month, day)


def _parse_lisp(text):
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


def _parse_text(xml):
    p = xml.findall('P')
    if len(p) == 0:
        p = [_parse_lisp(xml.text.strip())]
    else:
        p = [_parse_lisp(x.text.strip()) for x in p]
    return p


def _parse_mention(xml):
    return Mention(
        representative='representative' in xml.attrib,
        sentence=int(xml.find('sentence').text),
        start=int(xml.find('start').text),
        end=int(xml.find('end').text),
        head=int(xml.find('head').text))


def _parse_token(xml, simple_token=True):
    pos_tag = xml.find('POS')
    ner_tag = xml.find('NER')

    if simple_token:
        return Token(
                    id=xml.attrib['id'],
                    word=xml.find('word').text)
    else:
        return Token(
            id=xml.attrib['id'],
            word=xml.find('word').text,
            lemma=xml.find('lemma').text,
            begin=int(xml.find('CharacterOffsetBegin').text),
            end=int(xml.find('CharacterOffsetEnd').text),
            pos=pos_tag.text if pos_tag is not None else None,
            ner=ner_tag.text if ner_tag is not None else None)


def _parse_sentence(xml, simple_token=True):
    return Sentence(
        id=xml.attrib['id'],
        tokens=[_parse_token(x, simple_token) for x in xml.find('tokens')])


def read_file(path,
              parse_headline=True, parse_dateline=True,
              parse_coreferences=True, parse_sentences=True,
              parse_text=True, simple_token=True):
    with gzip.open(path, 'rt') as source:
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
                date = _parse_ymd(date_str)

                headline_xml = xml.find('HEADLINE')
                if headline_xml and parse_headline:
                    headline = _parse_lisp(headline_xml.text.strip())
                else:
                    headline = None

                dateline_xml = xml.find('DATELINE')
                if dateline_xml and parse_dateline:
                    dateline = _parse_lisp(dateline_xml.text.strip())
                else:
                    dateline = None

                coreferences = xml.find('coreferences')
                if coreferences and parse_coreferences:
                    coreferences = [[_parse_mention(m) for m in x]
                                    for x in coreferences]
                else:
                    coreferences = []

                sentences = xml.find('sentences')
                if sentences and parse_sentences:
                    sentences = [_parse_sentence(x, simple_token)
                                 for x in xml.find('sentences')]
                else:
                    sentences = []

                text = xml.find('TEXT')
                if text and parse_text:
                    text = _parse_text(text)
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
