import itertools


def group_ne_tokens(sentence, skip_tags=set([])):
    for r in itertools.groupby(sentence.tokens, key=lambda t: t.ner):
        if r[0] not in skip_tags:
            yield (r[0], list(r[1]))
