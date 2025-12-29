# -----------------------------
# FIRST & FOLLOW (Iterative)
# Input: paste  grammar = {...}
# -----------------------------

EPS = 'ε'
END = '$'


def read_grammar_from_stdin():
    print("Paste grammar dictionary (grammar = {...}) then press Enter on empty line:\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)

    text = "\n".join(lines)

    env = {}
    exec(text, {}, env)  # expects 'grammar' variable

    if "grammar" not in env:
        raise ValueError("You must paste something like: grammar = {...}")

    raw = env["grammar"]  # e.g. {'E': ["T E'", ...], ...}

    # Normalize productions: each production becomes a list of symbols
    grammar = {}
    for A, prods in raw.items():
        grammar[A] = []
        for p in prods:
            p = p.strip()
            if p == EPS:
                grammar[A].append([EPS])
            else:
                # split by spaces -> ['T', "E'"] or ['id']
                grammar[A].append(p.split())

    return grammar


def get_terminals_and_nonterminals(grammar):
    non_terminals = set(grammar.keys())
    terminals = set()

    for prods in grammar.values():
        for prod in prods:
            for sym in prod:
                if sym != EPS and sym not in non_terminals:
                    terminals.add(sym)

    return terminals, non_terminals


def first_of_sequence(seq, FIRST, non_terminals):
    """
    FIRST(seq) using already-known FIRST sets.
    seq is a list like ['T', "E'"] or ['id'].
    """
    if not seq:
        return {EPS}

    if len(seq) == 1 and seq[0] == EPS:
        return {EPS}

    result = set()

    for x in seq:
        fx = FIRST[x] if x in non_terminals else {x}  # terminal -> itself
        result |= (fx - {EPS})

        if EPS not in fx:
            break
    else:
        # all symbols can produce EPS
        result.add(EPS)

    return result


def compute_first_sets(grammar, non_terminals):
    FIRST = {A: set() for A in non_terminals}

    changed = True
    while changed:
        changed = False

        for A, prods in grammar.items():
            for prod in prods:
                add = first_of_sequence(prod, FIRST, non_terminals)
                before = len(FIRST[A])
                FIRST[A] |= add
                if len(FIRST[A]) != before:
                    changed = True

    return FIRST


def compute_follow_sets(grammar, FIRST, non_terminals, start_symbol):
    FOLLOW = {A: set() for A in non_terminals}
    FOLLOW[start_symbol].add(END)

    changed = True
    while changed:
        changed = False

        for A, prods in grammar.items():
            for prod in prods:
                for i, B in enumerate(prod):
                    if B not in non_terminals:
                        continue

                    beta = prod[i + 1:]
                    first_beta = first_of_sequence(beta, FIRST, non_terminals)

                    # Rule 1: FIRST(beta) - {EPS} ⊆ FOLLOW(B)
                    before = len(FOLLOW[B])
                    FOLLOW[B] |= (first_beta - {EPS})
                    if len(FOLLOW[B]) != before:
                        changed = True

                    # Rule 2: if EPS in FIRST(beta), FOLLOW(A) ⊆ FOLLOW(B)
                    if EPS in first_beta:
                        before = len(FOLLOW[B])
                        FOLLOW[B] |= FOLLOW[A]
                        if len(FOLLOW[B]) != before:
                            changed = True

    return FOLLOW


def pretty_set(s):
    # Force single-quotes around each item: {'(', 'id'}
    items = [f"'{x}'" for x in sorted(s)]
    return "{" + ", ".join(items) + "}"


def main():
    grammar = read_grammar_from_stdin()
    terminals, non_terminals = get_terminals_and_nonterminals(grammar)
    start_symbol = next(iter(grammar.keys()))  # first rule's LHS

    FIRST = compute_first_sets(grammar, non_terminals)
    FOLLOW = compute_follow_sets(grammar, FIRST, non_terminals, start_symbol)

    print("\n=== FIRST ===")
    for A in grammar.keys():
        print(f"FIRST({A}) = {pretty_set(FIRST[A])}")

    print("\n=== FOLLOW ===")
    for A in grammar.keys():
        print(f"FOLLOW({A}) = {pretty_set(FOLLOW[A])}")


if __name__ == "__main__":
    main()
