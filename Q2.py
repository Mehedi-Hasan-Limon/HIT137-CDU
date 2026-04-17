"""
HIT137 Assignment 2 - Question 2
Expression evaluator using recursive descent parsing.

Supports:
    Binary operators:   +  -  *  /
    Unary negation:     -5, --5, -(3+4), 3 * -2
    Parentheses:        nested to any depth
    Implicit multiply:  2(3+1), (1+2)(3+4), 3(4)  -- shown as * in the tree

Rejected:
    Unary + (e.g. "+5")
    Any character that is not a digit, dot, +, -, *, /, (, ), or whitespace

Public entry point:
    evaluate_file(input_path: str) -> list[dict]
        Reads expressions (one per line) from `input_path`, writes `output.txt`
        into the same directory, and returns a list of dicts:
            {"input": str, "tree": str, "tokens": str, "result": float | "ERROR"}

No classes are used. Each precedence level has its own parse function and
parenthesised sub-expressions recurse back to the top.
"""

import os


# ============================================================================
# TOKENIZER
# ============================================================================
# Tokens are plain tuples: (TYPE, value_str).
# Types: "NUM", "OP", "LPAREN", "RPAREN", "END".

def tokenize(text: str) -> list:
    """Turn a raw expression string into a list of tokens ending in END.

    Raises ValueError on any invalid character or malformed number.
    """
    tokens = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Skip whitespace.
        if ch.isspace():
            i += 1
            continue

        # Numbers: a run of digits, optionally with a single dot.
        if ch.isdigit() or (ch == '.' and i + 1 < n and text[i + 1].isdigit()):
            start = i
            dot_seen = (ch == '.')
            i += 1
            while i < n and (text[i].isdigit() or (text[i] == '.' and not dot_seen)):
                if text[i] == '.':
                    dot_seen = True
                i += 1
            # After consuming a number, a stray '.' immediately following it
            # (e.g. "3..5") is malformed.
            if i < n and text[i] == '.':
                raise ValueError(f"invalid number literal near {text[start:i+1]!r}")
            num_str = text[start:i]
            try:
                float(num_str)
            except ValueError:
                raise ValueError(f"invalid number literal: {num_str!r}")
            tokens.append(("NUM", num_str))
            continue

        # Operators.
        if ch in "+-*/":
            tokens.append(("OP", ch))
            i += 1
            continue

        # Parentheses.
        if ch == '(':
            tokens.append(("LPAREN", "("))
            i += 1
            continue
        if ch == ')':
            tokens.append(("RPAREN", ")"))
            i += 1
            continue

        # Anything else is invalid.
        raise ValueError(f"unexpected character: {ch!r}")

    tokens.append(("END", ""))
    return tokens


def format_tokens(tokens: list) -> str:
    """Render a token list as '[TYPE:value] [TYPE:value] ... [END]'."""
    parts = []
    for ttype, val in tokens:
        if ttype == "END":
            parts.append("[END]")
        else:
            parts.append(f"[{ttype}:{val}]")
    return " ".join(parts)


# ============================================================================
# PARSER  (recursive descent)
# ============================================================================
# The parser consumes a list of tokens and produces an AST built from nested
# tuples:
#     ("NUM", value_str)                 -- a numeric literal
#     ("BIN", op, left, right)           -- a binary operation
#     ("NEG", operand)                   -- unary negation
#
# A small mutable state dict {"tokens": [...], "pos": int} is threaded through
# every parse function since we are not allowed to use classes.
#
# Grammar (each level is a separate function):
#     expression := term     (('+' | '-') term)*
#     term       := factor   (('*' | '/') factor)*         -- also handles
#                                                             implicit multiply
#     factor     := '-' factor | primary
#     primary    := NUM | '(' expression ')'


def _peek(state):
    return state["tokens"][state["pos"]]


def _advance(state):
    tok = state["tokens"][state["pos"]]
    state["pos"] += 1
    return tok


def parse(tokens: list):
    """Parse the given tokens into an AST. Raises ValueError on any issue."""
    if not tokens or tokens[-1][0] != "END":
        raise ValueError("token stream missing END sentinel")

    state = {"tokens": tokens, "pos": 0}
    tree = _parse_expression(state)

    if _peek(state)[0] != "END":
        raise ValueError(f"unexpected token after expression: {_peek(state)!r}")
    return tree


def _parse_expression(state):
    """Lowest precedence: + and -, left associative."""
    node = _parse_term(state)
    while True:
        ttype, val = _peek(state)
        if ttype == "OP" and val in ("+", "-"):
            _advance(state)
            right = _parse_term(state)
            node = ("BIN", val, node, right)
        else:
            break
    return node


def _parse_term(state):
    """Higher precedence: * and /. Also handles implicit multiplication.

    Implicit multiplication fires when a factor is immediately followed by
    another factor without an intervening operator -- e.g. 2(3+1) or
    (1+2)(3+4). We detect this by looking ahead: if the next token starts a
    new factor (NUM or LPAREN), we treat it as a '*'.
    """
    node = _parse_factor(state)
    while True:
        ttype, val = _peek(state)
        if ttype == "OP" and val in ("*", "/"):
            _advance(state)
            right = _parse_factor(state)
            node = ("BIN", val, node, right)
        elif ttype in ("NUM", "LPAREN"):
            # Implicit multiplication: glue the next factor on as if '*'.
            right = _parse_factor(state)
            node = ("BIN", "*", node, right)
        else:
            break
    return node


def _parse_factor(state):
    """Unary '-' (any depth) or a primary. Unary '+' is not allowed."""
    ttype, val = _peek(state)
    if ttype == "OP" and val == "-":
        _advance(state)
        return ("NEG", _parse_factor(state))
    if ttype == "OP" and val == "+":
        raise ValueError("unary + is not supported")
    return _parse_primary(state)


def _parse_primary(state):
    """A number literal or a parenthesised expression."""
    ttype, val = _advance(state)

    if ttype == "NUM":
        return ("NUM", val)

    if ttype == "LPAREN":
        inner = _parse_expression(state)
        close_type, close_val = _advance(state)
        if close_type != "RPAREN":
            raise ValueError(f"expected ')', got {close_val!r}")
        return inner

    raise ValueError(f"unexpected token {val!r} ({ttype})")


# ============================================================================
# TREE RENDERING
# ============================================================================

def _format_number_for_tree(num_str: str) -> str:
    """Render a number literal: whole numbers without a trailing '.0'."""
    value = float(num_str)
    if value == int(value):
        return str(int(value))
    return str(value)


def render_tree(node) -> str:
    """Render an AST node in Lisp-like form:
        NUM       -> "3"
        BIN op    -> "(op left right)"
        NEG       -> "(neg operand)"
    """
    kind = node[0]
    if kind == "NUM":
        return _format_number_for_tree(node[1])
    if kind == "BIN":
        _, op, left, right = node
        return f"({op} {render_tree(left)} {render_tree(right)})"
    if kind == "NEG":
        return f"(neg {render_tree(node[1])})"
    raise ValueError(f"unknown node kind: {kind!r}")


# ============================================================================
# EVALUATOR
# ============================================================================

def evaluate(node) -> float:
    """Compute the numeric value of an AST. Raises ZeroDivisionError as-is."""
    kind = node[0]
    if kind == "NUM":
        return float(node[1])
    if kind == "NEG":
        return -evaluate(node[1])
    if kind == "BIN":
        _, op, left, right = node
        lv = evaluate(left)
        rv = evaluate(right)
        if op == "+":
            return lv + rv
        if op == "-":
            return lv - rv
        if op == "*":
            return lv * rv
        if op == "/":
            if rv == 0:
                raise ZeroDivisionError("division by zero")
            return lv / rv
    raise ValueError(f"unknown node kind: {kind!r}")


def _format_result(value: float) -> str:
    """Whole numbers as integers (8 not 8.0); otherwise rounded to 4dp."""
    if value == int(value):
        return str(int(value))
    return str(round(value, 4))


# ============================================================================
# PUBLIC API
# ============================================================================

def evaluate_file(input_path: str) -> list:
    """Read expressions, write output.txt alongside the input, return results.

    Each element of the returned list is a dict with keys:
        input  -> original line (str)
        tree   -> parse tree rendering or "ERROR"
        tokens -> token string or "ERROR"
        result -> float on success, "ERROR" on failure
    """
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    results = []
    for raw in raw_lines:
        line = raw.rstrip("\r\n")
        if line.strip() == "":
            # Skip blank lines entirely.
            continue

        entry = {"input": line, "tree": "ERROR", "tokens": "ERROR",
                 "result": "ERROR"}

        # --- Tokenize -------------------------------------------------------
        try:
            tokens = tokenize(line)
        except ValueError:
            results.append(entry)
            continue
        entry["tokens"] = format_tokens(tokens)

        # --- Parse ----------------------------------------------------------
        try:
            tree = parse(tokens)
        except ValueError:
            # Keep tokens (they were valid lexically), but tree + result fail.
            entry["tree"] = "ERROR"
            entry["result"] = "ERROR"
            results.append(entry)
            continue
        entry["tree"] = render_tree(tree)

        # --- Evaluate -------------------------------------------------------
        try:
            value = evaluate(tree)
        except ZeroDivisionError:
            entry["result"] = "ERROR"
            results.append(entry)
            continue
        except ValueError:
            entry["result"] = "ERROR"
            results.append(entry)
            continue
        entry["result"] = float(value)
        results.append(entry)

    # --- Write output.txt ---------------------------------------------------
    out_dir = os.path.dirname(os.path.abspath(input_path))
    out_path = os.path.join(out_dir, "output.txt")

    blocks = []
    for r in results:
        if isinstance(r["result"], str):
            result_str = r["result"]          # "ERROR"
        else:
            result_str = _format_result(r["result"])
        blocks.append(
            f"Input: {r['input']}\n"
            f"Tree: {r['tree']}\n"
            f"Tokens: {r['tokens']}\n"
            f"Result: {result_str}"
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(blocks) + "\n")

    return results


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_input.txt"
    evaluate_file(path)
    print(f"Done. Output written to {os.path.join(os.path.dirname(os.path.abspath(path)), 'output.txt')}")


if __name__ == "__main__":
    main()
