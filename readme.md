# HIT137 — Group Assignment 2 (S1 2026)

**Author:** Mehedi Hasan Limon (S395858)

Python solutions for the two programming tasks: a text encryption/decryption tool and a recursive-descent expression evaluator.

## Repository layout

```
.
├── Q1/
│   ├── encryption.py      # encrypt + decrypt + verify
│   └── raw_text.txt       # input plaintext
├── Q2/
│   ├── evaluator.py       # tokenizer, parser, evaluator
│   ├── sample_input.txt   # provided test input
│   └── output.txt         # generated output
├── github_link.txt
└── README.md
```

## Requirements

- Python 3.10+
- No third-party packages.

---

## Question 1 — Encryption / Decryption

Reads `raw_text.txt`, encrypts it using two user-supplied shift values, decrypts the result, and verifies that the round-trip matches the original.

### Encryption rules

| Characters      | Shift                       |
| --------------- | --------------------------- |
| lowercase a–m   | forward by `shift1 * shift2` |
| lowercase n–z   | backward by `shift1 + shift2` |
| uppercase A–M   | backward by `shift1`        |
| uppercase N–Z   | forward by `shift2²`        |
| everything else | unchanged                   |

### Run

```bash
cd Q1
python encryption.py
```

Enter `shift1` and `shift2` when prompted. The program creates:

- `encrypted_text.txt` — ciphertext
- `decrypted_text.txt` — recovered plaintext
- `cipher_map.txt` — per-letter rule tag used for exact inversion
- Prints `Verification SUCCESS` or `FAILED`

### Note on `cipher_map.txt`

The two lowercase rules use different shift amounts, so a shifted letter can cross the `a–m` / `n–z` boundary, making the source rule unrecoverable from the ciphertext alone. The encryption step records which rule applied to each original letter in `cipher_map.txt`, which the decryption step uses to invert the exact rule. This guarantees a perfect round-trip for any input and any shift values.

---

## Question 2 — Expression Evaluator

Reads one expression per line from an input file, evaluates each using recursive-descent parsing, and writes `output.txt` to the same directory.

### Features

- Binary operators: `+`, `-`, `*`, `/`
- Unary negation at any depth: `-5`, `--5`, `-(3+4)`, `3 * -2`
- Parentheses nested to any depth
- Implicit multiplication: `2(3+1)`, `(1+2)(3+4)`
- Unary `+` is rejected (`ERROR`)
- Division by zero and invalid characters produce `ERROR` without crashing

### Run

```bash
cd Q2
python evaluator.py sample_input.txt
```

### Required interface

```python
def evaluate_file(input_path: str) -> list[dict]
```

Returns a list of dicts, one per expression:

```python
{"input": "3 + 5", "tree": "(+ 3 5)",
 "tokens": "[NUM:3] [OP:+] [NUM:5] [END]", "result": 8.0}
```

`result` is a `float` on success or the string `"ERROR"` on failure.

### Output format

Each expression produces a four-line block, separated by a blank line:

```
Input: 3 + 5
Tree: (+ 3 5)
Tokens: [NUM:3] [OP:+] [NUM:5] [END]
Result: 8
```

Whole numbers display without `.0`; other results are rounded to 4 decimal places.

### Architecture (no classes)

| Level            | Function             | Handles                |
| ---------------- | -------------------- | ---------------------- |
| expression       | `_parse_expression`  | `+`, `-`               |
| term             | `_parse_term`        | `*`, `/`, implicit `*` |
| factor           | `_parse_factor`      | unary `-`              |
| primary          | `_parse_primary`     | `NUM`, `( ... )`       |

Parentheses recurse back to `_parse_expression`.

---

## Testing

- **Q1:** round-trip verified on the provided `raw_text.txt` and on a synthetic string containing every letter, digit, and common punctuation, across 13 shift pairs including `(0,0)`, `(13,13)`, `(25,25)`, and `(100,100)`.
- **Q2:** byte-for-byte exact match against `sample_output.txt`; 21 additional edge cases pass (deep unary, implicit multiplication, trailing operators, unmatched parentheses, malformed numbers, division by zero, invalid characters).
