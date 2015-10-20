import itertools
from collections import namedtuple

NamedEntity = namedtuple('NamedEntity', 'type start end text')


def group_ne_tokens(sentence, skip_tags=set([])):
    for r in itertools.groupby(sentence.tokens, key=lambda t: t.ner):
        if r[0] not in skip_tags:
            yield (r[0], list(r[1]))


def get_named_entities(sentence, skip_tags=set([])):
    for g in group_ne_tokens(sentence, skip_tags=skip_tags):
        ne_type = g[0]
        ne_start = g[1][0].id
        ne_end = g[1][-1].id
        ne_text = ' '.join(x.word for x in g[1])
        yield NamedEntity(ne_type, ne_start, ne_end, ne_text)
