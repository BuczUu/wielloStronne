import hashlib
import secrets
import random
from typing import Dict, Set, Tuple

def H(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def commit_color(vertex: int, color_label: int, nonce: bytes, round_id: int) -> str:
    # hash zawiera vertex_id, kolor, nonce i round_id
    return H(vertex.to_bytes(4, 'big') + color_label.to_bytes(1, 'big') + nonce + round_id.to_bytes(4, 'big'))

class Prover:
    def __init__(self, graph: Dict[int, Set[int]], coloring: Dict[int,int]):
        self.graph = graph
        self.coloring = coloring

    def prepare_round(self, round_id: int) -> Dict[int,str]:
        # losowa permutacja kolorów
        perm = list(range(3))
        random.shuffle(perm)
        self._last_perm = perm
        self._last_nonces = {}
        self._last_commitments = {}
        for v in self.graph:
            color = perm[self.coloring[v]]
            nonce = secrets.token_bytes(16)
            self._last_nonces[v] = nonce
            self._last_commitments[v] = commit_color(v, color, nonce, round_id)
        return self._last_commitments

    def respond_challenge(self, edge: Tuple[int,int]) -> Dict[int, Tuple[int, bytes]]:
        u, v = edge
        perm = self._last_perm
        return {
            u: (perm[self.coloring[u]], self._last_nonces[u]),
            v: (perm[self.coloring[v]], self._last_nonces[v])
        }

class Verifier:
    def __init__(self, graph: Dict[int, Set[int]]):
        self.graph = graph

    def choose_edge(self) -> Tuple[int,int]:
        edges = [(u, v) for u in self.graph for v in self.graph[u] if u < v]
        return random.choice(edges)

    def check_openings(self, commitments: Dict[int,str], round_id: int, openings: Dict[int, Tuple[int, bytes]]) -> bool:
        keys = list(openings.keys())
        if len(keys) != 2:
            return False
        u, v = keys
        pu, nonce_u = openings[u]
        pv, nonce_v = openings[v]
        print(f"Sprawdzanie krawędzi ({u}, {v}) z kolorami {pu}, {pv}")
        if commit_color(u, pu, nonce_u, round_id) != commitments[u]:
            print("Hash mismatch u")
            return False
        if commit_color(v, pv, nonce_v, round_id) != commitments[v]:
            print("Hash mismatch v")
            return False
        if pu == pv:
            print("Kolory dla krawędzi takie same!")
            return False
        return True

def run_protocol(graph: Dict[int, Set[int]], prover: Prover, rounds: int):
    verifier = Verifier(graph)
    accepted = True
    for r in range(1, rounds+1):
        commitments = prover.prepare_round(r)
        edge = verifier.choose_edge()
        openings = prover.respond_challenge(edge)
        ok = verifier.check_openings(commitments, r, openings)
        print(f"Runda {r}, edge {edge}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            accepted = False
            break
    if accepted:
        print(f"Sukces po {rounds} rundach")
    else:
        print("Oszustwo")


class Cheater(Prover):
    def __init__(self, graph: Dict[int, Set[int]]):
        # losowe kolorowanie
        fake_coloring = {v: random.randint(0,2) for v in graph}
        self.graph = graph
        self.coloring = fake_coloring

if __name__ == "__main__":
    graph = {0:{1,5}, 1:{0,2,5}, 2:{1,5}, 3:{4,5}, 4:{3,5}, 5:{0,1,2,3,4}}
    rounds = 100  # np. 10*|E|

    coloring = {0:0, 1:1, 2:0, 3:0, 4:1, 5:2}
    prover = Prover(graph, coloring)
    print("Symulacja uczciwego:")
    run_protocol(graph, prover, rounds)

    cheater = Cheater(graph)
    print("\nSymulacja oszusta:")
    run_protocol(graph, cheater, rounds)
