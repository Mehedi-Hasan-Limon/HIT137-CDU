# ---------- helpers ---------------------------------------------------------

def _shift_within_half(ch: str, start: str, end: str, offset: int) -> str:
    size = ord(end) - ord(start) + 1
    return chr((ord(ch) - ord(start) + offset) % size + ord(start))


def _shift_in_case(ch: str, offset: int) -> str:
    if ch.islower():
        base = ord('a')
    else:
        base = ord('A')
    return chr((ord(ch) - base + offset) % 26 + base)


def _classify(ch: str) -> str:
    if 'a' <= ch <= 'm':
        return 'L'
    if 'n' <= ch <= 'z':
        return 'l'
    if 'A' <= ch <= 'M':
        return 'U'
    if 'N' <= ch <= 'Z':
        return 'u'
    return '.'


def _encrypt_char(ch: str, shift1: int, shift2: int):
    tag = _classify(ch)
    if tag == 'L':
        return _shift_in_case(ch,  shift1 * shift2), tag
    if tag == 'l':
        return _shift_in_case(ch, -(shift1 + shift2)), tag
    if tag == 'U':
        return _shift_in_case(ch, -shift1), tag
    if tag == 'u':
        return _shift_in_case(ch,  shift2 ** 2), tag
    return ch, tag


def _decrypt_char(ch: str, tag: str, shift1: int, shift2: int) -> str:
    if tag == 'L':
        return _shift_in_case(ch, -(shift1 * shift2))
    if tag == 'l':
        return _shift_in_case(ch,  (shift1 + shift2))
    if tag == 'U':
        return _shift_in_case(ch,  shift1)
    if tag == 'u':
        return _shift_in_case(ch, -(shift2 ** 2))
    return ch                                    # unchanged


# ---------- main operations -------------------------------------------------

def encrypt_file(shift1: int, shift2: int,
                 src_path: str = "raw_text.txt",
                 dst_path: str = "encrypted_text.txt",
                 map_path: str = "cipher_map.txt") -> None:

    with open(src_path, "r", encoding="utf-8") as f:
        plaintext = f.read()

    encrypted_chars = []
    tags = []
    for ch in plaintext:
        enc, tag = _encrypt_char(ch, shift1, shift2)
        encrypted_chars.append(enc)
        if tag != '.':
            tags.append(tag)

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write("".join(encrypted_chars))

    # Save the rule tags for every letter, in order, as one string.
    with open(map_path, "w", encoding="utf-8") as f:
        f.write("".join(tags))


def decrypt_file(shift1: int, shift2: int,
                 src_path: str = "encrypted_text.txt",
                 dst_path: str = "decrypted_text.txt",
                 map_path: str = "cipher_map.txt") -> None:
    with open(src_path, "r", encoding="utf-8") as f:
        ciphertext = f.read()
    with open(map_path, "r", encoding="utf-8") as f:
        tags = f.read()

    out = []
    tag_idx = 0
    for ch in ciphertext:
        if ch.isalpha():
            tag = tags[tag_idx]
            tag_idx += 1
            out.append(_decrypt_char(ch, tag, shift1, shift2))
        else:
            out.append(ch)

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write("".join(out))


def verify_decryption(raw_path: str = "raw_text.txt",
                      decrypted_path: str = "decrypted_text.txt") -> bool:

    with open(raw_path, "r", encoding="utf-8") as f:
        original = f.read()
    with open(decrypted_path, "r", encoding="utf-8") as f:
        decrypted = f.read()

    if original == decrypted:
        print("Verification SUCCESS: decrypted text matches the original.")
        return True

    print("Verification FAILED: decrypted text does NOT match the original.")
    # Show the first difference to help debugging.
    for i, (a, b) in enumerate(zip(original, decrypted)):
        if a != b:
            print(f"  First difference at index {i}: "
                  f"original={a!r}, decrypted={b!r}")
            break
    if len(original) != len(decrypted):
        print(f"  Length differs: original={len(original)}, "
              f"decrypted={len(decrypted)}")
    return False


# ---------- entry point -----------------------------------------------------

def _read_positive_int(prompt: str) -> int:
    """Prompt until the user enters a non-negative integer."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value < 0:
                print("  Please enter a non-negative integer.")
                continue
            return value
        except ValueError:
            print("  Invalid input. Please enter an integer.")


def main() -> None:
    print("=== HIT137 Assignment 2 - Question 1 ===")
    shift1 = _read_positive_int("Enter shift1 (integer): ")
    shift2 = _read_positive_int("Enter shift2 (integer): ")

    encrypt_file(shift1, shift2)
    print("Encryption complete -> encrypted_text.txt")

    decrypt_file(shift1, shift2)
    print("Decryption complete -> decrypted_text.txt")

    verify_decryption()


if __name__ == "__main__":
    main()
