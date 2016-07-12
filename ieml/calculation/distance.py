import pprint
import itertools as it
from collections import defaultdict

from ieml.AST.propositions import Word, Sentence, SuperSentence
from ieml.AST.terms import Term
from ieml.AST.usl import Text, HyperText
from ieml.operator import usl
from bidict import bidict


def distance(uslA, uslB, weights):
    categories = bidict({Term: 1, Word: 2, Sentence: 3, SuperSentence: 4, Text: 5, HyperText: 6})


    def compute_stages(usl):
        '''
        Get all the elements in the usl by stages, Term, Word, Sentence, SSentence, Text, Hypertext
        :param usl:
        :return:
        '''
        def usl_iter(usl):
            for t in usl.texts:
                yield from t.tree_iter()

        stages = {c: set() for c in categories}

        for e in (k for k in usl_iter(b) if isinstance(k, tuple(categories))):
            stages[e.__class__].add(e)

        children = {}
        for cat in stages:
            for e in stages[cat]:
                if isinstance(e, Term):
                    children[e] = set()
                    continue

                if isinstance(e, (Word, Sentence, SuperSentence)):
                    _class = categories.inv[categories[e.__class__] - 1]
                    children[e] = set(i for i in e.tree_iter() if isinstance(i, _class))

                if isinstance(e, HyperText):
                    children[e] = set(e.texts)
                    continue

                if isinstance(e, Text):
                    children[e] = set(e.children)
                    continue


        result = defaultdict(lambda: defaultdict(lambda: 0))
        stack = [usl]
        for e in usl_iter(usl):
            if e.__class__ not in categories:
                continue

            while categories[e.__class__] >= categories[stack[-1].__class__]:
                stack.pop()

            for k in stack:
                result[k][e] += 1

            stack.append(e)

        return stages, children, result

    stages_A, children_A, children_multi_A = compute_stages(uslA)
    stages_B, children_B, children_multi_B = compute_stages(uslB)

    def EO(stage):
        if len(stages_A[stage] | stages_B[stage]) == 0:
            raise ValueError

        return float(len(stages_A[stage] & stages_B[stage])) / len(stages_A[stage] | stages_B[stage])

    def OO(stage):
        if stage is Term:
            raise ValueError

        size = float(len(stages_A[stage]) * len(stages_B[stage]))
        accum = 0.0
        for a, b in it.product(stages_A[stage], stages_B[stage]):
            accum += len(children_A[a] & children_B[b]) / (size * len(children_A[a] | children_B[b]))

        return accum

    def O_O(stage):
        pass

    def Oo(stage):
        result = {Sentence: 0, SuperSentence: 0, Text: 0, HyperText: 0}
        for a_st, b_st in it.permutations(categories.values(), 2):
            size = float(len(stages_A[a_st]) * len(stages_B[b_st]))
            accum = 0.0

            # if true b in a
            direct = categories[a_st] > categories[b_st]

            for a, b in it.product(stages_A[a_st], stages_B[b_st]):
                if direct:
                    accum += children_multi_A[a][b] / \
                             (size * len([e for e in children_multi_A[a] if e.__class__ == b.__class__]))
                else:
                    accum += children_multi_B[b][a] / \
                             (size * len([e for e in children_multi_B[b] if e.__class__ == a.__class__]))

            if direct:
                result[a_st] += accum / 2.0
            else:
                result[b_st] += accum / 2.0
        return result

if __name__ == '__main__':
    a = "{/[([a.i.-]+[i.i.-])*([E:A:T:.]+[E:S:.wa.-]+[E:S:.o.-])]//[([([a.i.-]+[i.i.-])*([E:A:T:.]+[E:S:.wa.-]+[E:S:.o.-])]{/[([a.i.-]+[i.i.-])*([E:A:T:.]+[E:S:.wa.-]+[E:S:.o.-])]/}*[([t.i.-s.i.-'i.B:.-U:.-'we.-',])*([E:O:.wa.-])]*[([E:E:T:.])])+([([a.i.-]+[i.i.-])*([E:A:T:.]+[E:S:.wa.-]+[E:S:.o.-])]*[([t.i.-s.i.-'u.B:.-A:.-'wo.-',])]*[([E:T:.f.-])])]/}"
    b = usl(a)
    c = usl(a)
    distance(b, c , None)