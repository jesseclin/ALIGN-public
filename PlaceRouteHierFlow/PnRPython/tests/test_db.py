import json
from pnrdb import hierNode, PnRDBEncoder

import io
import copy

def test_A():
    with open("tests/telescopic_ota-freeze.json","rt") as fp:
        j = json.load(fp)
        hN = hierNode(j)

    with io.StringIO() as fp:
        json.dump( hN, fp=fp, cls=PnRDBEncoder, indent=2)
        s = fp.getvalue()

    with io.StringIO(s) as fp:
        jj = json.load(fp)

    assert j == jj

def test_write():
    with open("tests/telescopic_ota-freeze.json","rt") as fp:
        j = json.load(fp)
        j_copy = copy.deepcopy(j)
        hN = hierNode(j)

    assert j['name'] == "telescopic_ota"

    hN.name = "treefrog"

    assert j['name'] == "treefrog"
    assert hN.name == "treefrog"

    with io.StringIO() as fp:
        json.dump( hN, fp=fp, cls=PnRDBEncoder, indent=2)
        s = fp.getvalue()

    with io.StringIO(s) as fp:
        jj = json.load(fp)

    assert jj['name'] == "treefrog"

    assert j == jj

    #
    # Some of the JSON changes (the leaves)
    #
    assert j_copy != j

    #
    # This is how it changed
    #
    j_copy['name'] = "treefrog"
    assert j_copy == j
