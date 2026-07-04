# Kernel de similarité cosinus vectorisé (SIMD) — représentatif du scoring RAG :
# retrouver, parmi N articles candidats, celui dont l'embedding colle le mieux à la
# question. Objectif : montrer que Mojo compile en natif arm64 et fait du calcul réel
# sur Apple Silicon, sans dépendre d'une lib BLAS d'un vendeur (le même code porte
# ensuite vers GPU NVIDIA/AMD via MAX).
#
# Les vecteurs sont générés par une formule déterministe, IDENTIQUE à la version
# Python (retrieval_similarity.py), pour vérifier que les deux trouvent le même
# best_idx (contrôle de correction inter-langage — l'esprit « de confiance »).
#
# Validé sur le toolchain Mojo installé localement (0.7.0). L'API Mojo évolue :
# pour un toolchain récent, adapter les imports (memory / SIMD) si besoin.

from memory.unsafe import DTypePointer
from math import sqrt
from time import now

alias F64 = DType.float64
alias nelts = 4  # largeur SIMD pour float64

fn fill(p: DTypePointer[F64], n: Int, salt: Int):
    for i in range(n):
        # déterministe, identique en Python : ((i*7 + salt) % 97) / 97
        p.store(i, Float64(((i * 7 + salt) % 97)) / 97.0)

fn dot(a: DTypePointer[F64], ao: Int, b: DTypePointer[F64], bo: Int, n: Int) -> Float64:
    var acc = SIMD[F64, nelts](0.0)
    var i = 0
    while i + nelts <= n:
        acc += a.simd_load[nelts](ao + i) * b.simd_load[nelts](bo + i)
        i += nelts
    var s = acc.reduce_add()
    while i < n:  # queue (dimension non multiple de nelts)
        s += a.load(ao + i) * b.load(bo + i)
        i += 1
    return s

fn main():
    let N = 2000      # articles candidats
    let D = 384       # dimension d'embedding
    let R = 50        # requêtes répétées (pour un temps mesurable)
    let docs = DTypePointer[F64].alloc(N * D)
    let q = DTypePointer[F64].alloc(D)
    let dnorm = DTypePointer[F64].alloc(N)

    for d in range(N):
        fill(docs.offset(d * D), D, d * 3 + 1)
    fill(q, D, 11)

    # normes des documents précalculées (comme à l'indexation)
    for d in range(N):
        dnorm.store(d, sqrt(dot(docs, d * D, docs, d * D, D)))
    let qn = sqrt(dot(q, 0, q, 0, D))

    var best_idx: Int = -1
    var best: Float64 = -1.0
    let t0 = now()
    for r in range(R):
        best_idx = -1
        best = -1.0
        for d in range(N):
            let s = dot(q, 0, docs, d * D, D) / (qn * dnorm.load(d))
            if s > best:
                best = s
                best_idx = d
    let t1 = now()

    let ms = Float64(t1 - t0) / 1.0e6
    print("MOJO  best_idx=", best_idx, " score=", best)
    print("MOJO  ms=", ms, " (", N * R, "comparaisons )")
    docs.free(); q.free(); dnorm.free()
