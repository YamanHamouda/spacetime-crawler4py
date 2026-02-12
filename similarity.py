import re
import hashlib

seen_hashes = set()
seen_sigs = []

# words per shingle/tiny text segment
K = 3

# how many numbers in the page fingerprint (bigger = more accurate)
N = 64

# if similarity >= this, then it is near-duplicate
THRESHOLD = 0.8

def is_duplicate_page(text):
    '''Return True if this page is an exact or near duplicate of a page the crawler already saw'''
    if not text:
        return False

    if not isinstance(text, str):
        return False

    norm = text.strip().lower()
    norm = re.sub(r"\s+", " ", norm)
    if not norm:
        return False

    data = norm.encode("utf-8")
    h = hashlib.sha256(data).hexdigest()
    if h in seen_hashes:
        return True

    word_pattern = r"[a-zA-Z0-9]+"
    words = re.findall(word_pattern, norm)
    shingles = set()
    for i in range(len(words) - K + 1):
        shingles.add(" ".join(words[i : i + K]))

    if not shingles:
        seen_hashes.add(h)
        return False

    sig = []
    for i in range(N):
        best = None
        for s in shingles:
            data = (str(i) + s).encode()
            hex_str = hashlib.sha256(data).hexdigest()
            val = int(hex_str, 16) % (2**32)
            if best is None or val < best:
                best = val
        sig.append(best)
        
    sig = tuple(sig)

    for old in seen_sigs:
        same = 0
        for a, b in zip(sig, old):
            if a == b:
                same += 1
                
        if same / N >= THRESHOLD:
            return True

    seen_hashes.add(h)
    seen_sigs.append(sig)

    return False