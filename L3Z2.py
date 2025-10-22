import math
import random
from sympy import randprime
import hashlib


def egcd(a, b):
    # Extended Euclidean Algorithm
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)


def modinv(a, m):
    # Modular Inverse using Extended Euclidean Algorithm
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m


def randomZnElement(N):
    # Returns a random element in Z_N^*
    g = N
    while math.gcd(g, N) != 1:
        g = random.randint(2, N)
    return g


def GenModulus(w):
    # Generates RSA modulus N of bit-length w
    n = len(w) // 2
    p = randprime(2 ** n, 2 ** (n + 1))
    q = randprime(2 ** n, 2 ** (n + 1))
    N = p * q
    return N, p, q


def GenRSA(w):
    # Generates RSA keys of bit-length w
    n = len(w)
    N, p, q = GenModulus(w)
    m = (p - 1) * (q - 1)
    e = 2 ** 16 + 1
    d = modinv(e, m)
    return N, e, d, p, q


def check(n, x, a, e, b):
    # Static method to check the verification step
    left = (b ** 2) % n
    right = (a * (x ** e)) % n
    return left == right


class FSI_Prover:
    # Fiat-Shamir Identification Prover
    def __init__(self, w):
        self.w = w
        self.GenFSI(w)
        self.r = None
        self.a = None
        self.b = None

    def get_public_key(self):
        return self.n, self.x

    def GenFSI(self, w):
        # Generates keys for Fiat-Shamir Identification
        self.n, _, _, p, q = GenRSA(self.w)
        self.y = randomZnElement(self.n)  # secret key
        self.x = (self.y ** 2) % self.n  # public key

    def FSI_Prover_Step_1_Commit(self):
        # Prover's first step in Fiat-Shamir Identification
        self.r = randomZnElement(self.n)
        a = (self.r ** 2) % self.n
        return a

    def FSI_Prover_Step_2_Response(self, e):
        # Prover's second step in Fiat-Shamir Identification
        b = (self.r * (self.y ** e)) % self.n
        return b


class FSI_Verifier:
    # Fiat-Shamir Identification Verifier

    def __init__(self, n, x):
        # Initializes the verifier with public key (n, x)
        self.n = n
        self.x = x
        self.e = None
        self.a = None
        self.b = None

    def FSI_Verifier_Step_1_Challenge(self, a):
        # Verifier's challenge in Fiat-Shamir Identification
        self.a = a
        e = random.randint(0, 1)
        self.e = e
        return e

    def FSI_Verifier_Step_2_Verify(self, b):
        # Verifier's second step in Fiat-Shamir Identification
        left = (b ** 2) % self.n
        right = (self.a * (self.x ** self.e)) % self.n
        return left == right


class FSI:
    # Fiat-Shamir Identification Protocol

    def __init__(self, w, rounds=4):
        # Initializes the protocol with bit-length w and number of rounds
        self.w = w
        self.rounds = rounds

    def run(self):
        # Runs the Fiat-Shamir Identification protocol

        self.prover = FSI_Prover(self.w)

        n, x = self.prover.get_public_key()
        print(f"Public key (n, x): ({n}, {x})\n")

        self.verifier = FSI_Verifier(n, x)

        fsi = {"public_key": (n, x), "rounds": self.rounds, "transcript": []}
        transcript = []

        for i in range(self.rounds):
            print(f"Round {i + 1}")

            # Prover's first step
            a = self.prover.FSI_Prover_Step_1_Commit()
            print(f"Prover sends a: {a}")

            # Verifier's challenge
            e = self.verifier.FSI_Verifier_Step_1_Challenge(a)
            print(f"Verifier sends challenge e: {e}")

            # Prover's response
            b = self.prover.FSI_Prover_Step_2_Response(e)
            print(f"Prover sends response b: {b}")

            # Verifier's verification
            if self.verifier.FSI_Verifier_Step_2_Verify(b):
                print("Verification successful!\n")
                transcript.append({"a": a, "e": e, "b": b, "v": True})
            else:
                print("Verification failed!\n")
                transcript.append({"a": a, "e": e, "b": b, "v": False})
                return False

        fsi["transcript"] = transcript
        print(fsi)
        return True


class FSI_DishonestProver:
    # Fiat-Shamir Identification Dishonest Prover

    def __init__(self, n, x):
        self.n = n
        self.x = x
        self.r = None
        self.a = None
        self.b = None

    def get_public_key(self):
        return self.n, self.x

    def FSI_Prover_Step_1_Commit(self):
        # Prover's first step in Fiat-Shamir Identification
        # r is generated as in the honest prover
        self.r = randomZnElement(self.n)

        # P* tries to guess e in advance
        e = random.randint(0, 1)

        if e == 0:
            a = (self.r ** 2) % self.n
        else:
            a = (self.r ** 2 * modinv(self.x, self.n)) % self.n
        return a

    def FSI_Prover_Step_2_Response(self, e):
        # Dishonest Prover's second step in Fiat-Shamir Identification

        # Respond with r
        b = self.r
        # instead of: r * (y ** e) mod n
        # which would require knowing y
        # b = (self.r * (self.y ** e)) % self.n
        return b


class FSI_with_DishonestProver:
    # Fiat-Shamir Identification Protocol

    def __init__(self, w, rounds=20):
        # Initializes the protocol with bit-length w and number of rounds
        self.w = w
        self.rounds = rounds

    def run(self):
        # Runs the Fiat-Shamir Identification protocol

        self.honest_prover = FSI_Prover(self.w)

        n, x = self.honest_prover.get_public_key()
        print(f"Public key (n, x): ({n}, {x})\n")

        self.prover = FSI_DishonestProver(n, x)

        self.verifier = FSI_Verifier(n, x)

        fsi = {"public_key": (n, x), "rounds": self.rounds, "transcript": []}
        transcript = []

        for i in range(self.rounds):
            print(f"Round {i + 1}")

            # Prover's first step
            a = self.prover.FSI_Prover_Step_1_Commit()
            print(f"Prover sends a: {a}")

            # Verifier's challenge
            e = self.verifier.FSI_Verifier_Step_1_Challenge(a)
            print(f"Verifier sends challenge e: {e}")

            # Prover's response
            b = self.prover.FSI_Prover_Step_2_Response(e)
            print(f"Prover sends response b: {b}")

            # Verifier's verification
            if self.verifier.FSI_Verifier_Step_2_Verify(b):
                print("Verification successful!\n")
                transcript.append({"a": a, "e": e, "b": b, "v": True})
            else:
                print("Verification failed!\n")
                transcript.append({"a": a, "e": e, "b": b, "v": False})
                # return False

        fsi["transcript"] = transcript
        print(fsi)
        return True


# ==================== NIZKP ====================

class FiatShamirSignature:
    def __init__(self):
        self.context = None  # (n, x, y)

    def Gen(self, n):
        prover = FSI_Prover("1" * (n // 8))
        n_val, x = prover.get_public_key()
        y = prover.y
        self.context = (n_val, x, y)
        return (n_val, x), y

    def Sign(self, sk, m):
        n, x, stored_sk = self.context

        r = randomZnElement(n)
        a = pow(r, 2, n)

        challenge_input = a.to_bytes(256, 'big') + m
        e = int.from_bytes(hashlib.sha256(challenge_input).digest(), 'big') % (2 ** 256)

        b = (r * pow(sk, e, n)) % n
        return (a, b, e)

    def Verify(self, pk, m, sigma):
        n, x = pk
        a, b, e = sigma

        challenge_input = a.to_bytes(256, 'big') + m
        expected_e = int.from_bytes(hashlib.sha256(challenge_input).digest(), 'big') % (2 ** 256)

        if e != expected_e:
            print(f"{e} != {expected_e}")
            return False

        left = pow(b, 2, n)
        right = (a * pow(x, e, n)) % n

        print(f"Verification: {left} == {right}? {left == right}")
        return left == right


def test_signature_scheme():
    print("\n" + "=" * 60)
    print("TEST podpisy")
    print("=" * 60)

    fs_sig = FiatShamirSignature()

    # gen
    pk, sk = fs_sig.Gen(256)
    print(f"Public key (n, x): n={pk[0]}, x={pk[1]}")
    print(f"Secret key: y={sk}")

    # podpis wiadomości
    message = b"wiadomosccccccccc"
    signature = fs_sig.Sign(sk, message)
    print(f"Message: {message}")
    print(f"Signature: a={signature[0]}, b={signature[1]}, e={signature[2]}")

    # weryfikacja podpisu
    fs_sig.Verify(pk, message, signature)

    return True

def test_honest_prover():
    print("\n" + "=" * 50)
    print("TEST Honest")
    print("=" * 50)

    w = "1010101010101010"
    fsi = FSI(w, rounds=4)
    fsi.run()

    print("passed")


def test_dishonest_prover():
    print("\n" + "=" * 50)
    print("TEST Dishonest")
    print("=" * 50)

    w = "1010101010101010"
    fsi_dishonest = FSI_with_DishonestProver(w, rounds=20)
    result = fsi_dishonest.run()

    print(f"Dishonest (result: {result})")


def run_all_tests():
    print("Tests")
    print("=" * 60)

    tests = [
        test_honest_prover,
        test_dishonest_prover,
        test_signature_scheme,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
