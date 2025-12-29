
# 1) Token categories and globals

# KEYWORDS: reserved words the lexer will tag as 'keyword'
KEYWORDS = ['if', 'for', 'while']

# RELOPS: relational operators (note multi-char ops are included)
RELOPS = ['<=', '>=', '!=', '==', '<', '>']

# OPERATORS: single-character arithmetic/assignment operators
OPERATORS = ['+', '-', '*', '=']

# SYMBOLS: punctuation used by the language (parentheses, colon)
SYMBOLS = ['(', ')', ':']

# symbol_table: a global set that collects all identifiers discovered by lexer
# using a set ensures each identifier appears only once in the table
symbol_table = set()


# -------------------------------
# 2) Helper functions
# -------------------------------

def is_letter(ch):
    """
    Return True if ch is an ASCII letter (a-z or A-Z).
    This is used to detect the start of identifiers/keywords.
    """
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z')


def is_digit(ch):
    """
    Return True if ch is a decimal digit (0-9).
    Used while scanning numeric tokens.
    """
    return '0' <= ch <= '9'


def is_keyword(token):
    """
    Check whether the extracted token string is one of the reserved keywords.
    This is a simple membership test against the KEYWORDS list.
    """
    return token in KEYWORDS


def is_identifier(token):
    """
    Validate whether token is a valid identifier according to these rules:
    - not empty
    - first character must be a letter or underscore
    - subsequent characters may be letters, digits, or underscore
    Returns True if token meets identifier rules, otherwise False.

    Note: In the lexer we already extract identifiers using similar rules,
    so this function can be used to re-validate or as a utility elsewhere.
    """
    if not token:
        return False
    if not (is_letter(token[0]) or token[0] == '_'):
        return False
    for ch in token[1:]:
        if not (is_letter(ch) or is_digit(ch) or ch == '_'):
            return False
    return True


def is_number(token):
    """
    Validate whether token is a valid numeric literal.
    Accepts:
      - integers (e.g., 123)
      - decimals (e.g., 3.14)
      - exponent notation (e.g., 1.2e-3, 5E+2)

    Rules enforced:
      - At most one '.' and only before an 'e'/'E'
      - At most one 'e' or 'E'
      - If 'e' is present, it must be followed by an optional '+' or '-'
        and then at least one digit.
      - Reject token '.' alone.
    """
    if not token:
        return False

    i = 0
    dot_count = 0
    e_count = 0

    while i < len(token):
        ch = token[i]

        if is_digit(ch):
            # any digit is always fine
            i += 1

        elif ch == '.':
            # '.' is allowed only once and only before any e/E
            dot_count += 1
            if dot_count > 1 or e_count > 0:
                return False
            i += 1

        elif ch in 'eE':
            # only one exponent marker allowed
            e_count += 1
            if e_count > 1:
                return False
            i += 1
            # optional sign right after e/E
            if i < len(token) and token[i] in '+-':
                i += 1
            # after e (and optional sign) there must be at least one digit
            if i >= len(token) or not is_digit(token[i]):
                return False

        else:
            # any other character inside token -> not a valid number
            return False

    # single dot is not a valid number
    if token == '.':
        return False

    return True


# -------------------------------
# 3) Main lexer function
# -------------------------------

def lexer(code):
    """
    Convert the input code (single string possibly with multiple lines)
    into a list of tokens of the form (type, lexeme).

    Token types used here:
      - 'keyword' : for reserved words in KEYWORDS
      - 'id'      : for identifiers (also added to symbol_table)
      - 'num'     : for numeric literals validated by is_number()
      - 'relop'   : for relational operators (<=, >=, ==, !=, <, >)
      - 'op'      : for single-character operators (+, -, *, =)
      - 'sym'     : for symbols like parentheses and colon
      - 'comment' : the rest of a line after '//' (kept as a single token)
      - 'ERROR'   : any malformed or unrecognized lexeme
    """
    tokens = []
    lines = code.split('\n')  # process input line-by-line for simplicity

    for line in lines:
        # strip leading/trailing whitespace so we don't treat indentation as tokens
        line = line.strip()
        if not line:
            # skip empty lines entirely
            continue

        # ---------- handle single-line comments ----------
        # We support '//' style comments. If '//' appears, separate comment text
        # and remove it from the line so the rest of the line is tokenized.
        comment_index = line.find('//')
        comment = ''
        if comment_index != -1:
            comment = line[comment_index:]
            line = line[:comment_index]

        # i is the current character index into the (possibly trimmed) line
        i = 0
        while i < len(line):
            ch = line[i]

            # skip whitespace characters between tokens
            if ch.isspace():
                i += 1
                continue

            # ---------- relational operators ----------
            # Check multi-character relational operators first (e.g., <=, >=, !=, ==)
            # We sort by length descending to ensure multi-char ops are matched before single-char ones.
            match = None
            for op in sorted(RELOPS, key=lambda x: -len(x)):
                if line[i:i + len(op)] == op:
                    match = op
                    break
            if match:
                tokens.append(('relop', match))
                i += len(match)
                continue

            # ---------- simple operators ----------
            # Single character arithmetic/assignment operators
            if ch in OPERATORS:
                tokens.append(('op', ch))
                i += 1
                continue

            # ---------- symbols/punctuation ----------
            if ch in SYMBOLS:
                tokens.append(('sym', ch))
                i += 1
                continue

            # ---------- identifiers & keywords ----------
            # If the character begins with a letter or underscore, we read an identifier
            # (letters, digits, underscores allowed in the body).
            if is_letter(ch) or ch == '_':
                j = i
                while j < len(line) and (is_letter(line[j]) or is_digit(line[j]) or line[j] == '_'):
                    j += 1
                token = line[i:j]
                # Distinguish keywords from identifiers
                if is_keyword(token):
                    tokens.append(('keyword', token))
                else:
                    tokens.append(('id', token))
                    symbol_table.add(token)  # record identifier in global symbol table
                i = j
                continue

            # ---------- numbers (improved extraction) ----------
            # We start number scanning only if current char is digit or dot.
            # The extraction logic is careful:
            #  - accept digits and at most one '.' (before any 'e')
            #  - allow optional exponent part with e/E and optional +/- immediately after e
            #  - do NOT allow '+' or '-' in arbitrary positions (only right after e)
            if is_digit(ch) or ch == '.':
                j = i
                seen_dot = False
                seen_e = False

                # Scan the integer/decimal part (before exponent)
                while j < len(line):
                    c = line[j]
                    if is_digit(c):
                        j += 1
                        continue
                    if c == '.' and not seen_dot and not seen_e:
                        seen_dot = True
                        j += 1
                        continue
                    break

                # If an exponent marker exists, process it (optional + or - allowed only here)
                if j < len(line) and line[j] in 'eE':
                    seen_e = True
                    j += 1
                    # optional sign after e/E
                    if j < len(line) and line[j] in '+-':
                        j += 1
                    # require at least one digit after e (is_number will catch missing digits)
                    start_digits_after_e = j
                    while j < len(line) and is_digit(line[j]):
                        j += 1
                    # if no digits after e, we still take the token as-is and let is_number flag it ERROR

                token = line[i:j]
                # Validate the constructed token using is_number (keeps validation logic centralized)
                if token and is_number(token):
                    tokens.append(('num', token))
                else:
                    # If token is empty (shouldn't happen) or invalid number, mark ERROR.
                    # This will also catch cases such as '5e' (no digits after e).
                    tokens.append(('ERROR', token if token else line[i]))
                i = j
                continue

            # ---------- fallback: unknown character ----------
            # If none of the above matched, mark the single character as ERROR and move on.
            tokens.append(('ERROR', ch))
            i += 1

        # after processing the non-comment portion of the line, append comment token if present
        if comment:
            tokens.append(('comment', comment))

    return tokens


# -------------------------------
# 4) Interactive driver: read user code and run lexer
# -------------------------------
if __name__ == '__main__':
    print("Enter your code (end with an empty line):")
    user_lines = []
    while True:
        try:
            line = input()
        except EOFError:
            # gracefully handle EOF (for e.g., piped input)
            break
        if line.strip() == "":
            break
        user_lines.append(line)

    user_code = '\n'.join(user_lines)
    output = lexer(user_code)

    print("\nTokens:")
    for typ, tok in output:
        print(f"{typ}({tok})")

    print("\nSymbol Table:", symbol_table)
