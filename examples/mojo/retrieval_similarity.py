# Même algo que retrieval_similarity.mojo, en Python pur + NumPy, sur le même Mac.
# Sert de point de comparaison honnête (Python pur = lisibilité, NumPy = BLAS vendeur).
# Le fill est identique au Mojo -> les deux doivent trouver le même best_idx.
#
#   python3 retrieval_similarity.py                 # Python pur (NumPy optionnel)
#   uv run --with numpy python retrieval_similarity.py   # + baseline NumPy

import time, math

N, D, R = 2000, 384, 50


def fill(n, salt):
    return [((i * 7 + salt) % 97) / 97.0 for i in range(n)]


docs = [fill(D, d * 3 + 1) for d in range(N)]
q = fill(D, 11)


def dot(a, b):
    s = 0.0
    for i in range(len(a)):
        s += a[i] * b[i]
    return s


dnorm = [math.sqrt(dot(v, v)) for v in docs]
qn = math.sqrt(dot(q, q))

t0 = time.perf_counter()
best_idx, best = -1, -1.0
for r in range(R):
    best_idx, best = -1, -1.0
    for d in range(N):
        s = dot(q, docs[d]) / (qn * dnorm[d])
        if s > best:
            best, best_idx = s, d
t1 = time.perf_counter()
print(f"PY    best_idx= {best_idx}  score= {best}")
print(f"PY    ms= {(t1 - t0) * 1000:.3f}  ( {N * R} comparaisons )")

# Baseline NumPy (BLAS vectorisé) si dispo
try:
    import numpy as np

    Dn = np.array(docs)
    qv = np.array(q)
    dn = np.linalg.norm(Dn, axis=1)
    qnv = np.linalg.norm(qv)
    t0 = time.perf_counter()
    for r in range(R):
        sims = Dn @ qv / (dn * qnv)
        bi = int(np.argmax(sims))
    t1 = time.perf_counter()
    print(f"NUMPY best_idx= {bi}  score= {sims[bi]}")
    print(f"NUMPY ms= {(t1 - t0) * 1000:.3f}  ( {N * R} comparaisons )")
except Exception as e:
    print("NUMPY indisponible:", e)
