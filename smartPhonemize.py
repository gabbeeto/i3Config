#!/usr/bin/env python3
"""
smart-phonemize: IPA with weak forms (British default, -us for American)
Usage: echo "text" | smart-phonemize [-us] [-uk] [-h]
  Default: British English (en-gb)
  -us  : American English (en-us)
  -uk  : explicit British (same as default)
  -h   : show this help
"""

import sys
import re
import subprocess

# ---- Weak form dictionaries ------------------------------------------------
# American English (rhotic)
WEAK_US = {
    'ænd': 'ənd',   # and
    'fɔr': 'fər',   # for
    'tu': 'tə',     # to
    'æt': 'ət',     # at
    'æz': 'əz',     # as
    'ðæt': 'ðət',   # that (conjunction)
    'ðən': 'ðən',   # than
    'ðɛr': 'ðɚ',    # there
    'hæz': 'həz',   # has
    'wʌz': 'wəz',   # was
    'wɜr': 'wɚ',    # were
    'jʊr': 'jɚ',    # your
    'ɑr': 'ɚ',      # are
    'hɜr': 'hɚ',    # her
    'miː': 'mi',    # me
    'juː': 'jə',    # you
    'hɪm': 'ɪm',    # him (consonant elision, optional)
    'ʌs': 'əs',     # us
    'ðɛm': 'ðəm',   # them
    'kæn': 'kən',   # can
    'wɪl': 'wəl',   # will
    'mʌst': 'məst', # must
    'ʌv': 'əv',     # of
}

# British English (non-rhotic)
WEAK_UK = {
    'ænd': 'ənd',   # and
    'fɔː': 'fə',    # for
    'tu': 'tə',     # to
    'æt': 'ət',     # at
    'æz': 'əz',     # as
    'ðæt': 'ðət',   # that
    'ðən': 'ðən',   # than
    'ðeə': 'ðə',    # there
    'hæz': 'həz',   # has
    'wɒz': 'wəz',   # was
    'wɜː': 'wə',    # were
    'jɔː': 'jə',    # your
    'ɑː': 'ə',      # are
    'hɜː': 'hə',    # her
    'miː': 'mi',    # me
    'juː': 'jə',    # you
    'hɪm': 'ɪm',    # him
    'ʌs': 'əs',     # us
    'ðɛm': 'ðəm',   # them
    'kæn': 'kən',   # can
    'wɪl': 'wəl',   # will
    'mʌst': 'məst', # must
    'ɒv': 'əv',     # of
}

# ---- Fallback: orthographic word -> strong IPA (for missing pronunciations) ----
ORTHO_TO_IPA_UK = {
    'and': 'ænd', 'for': 'fɔː', 'to': 'tuː', 'at': 'æt', 'as': 'æz',
    'that': 'ðæt', 'than': 'ðən', 'there': 'ðeə', 'has': 'hæz',
    'was': 'wɒz', 'were': 'wɜː', 'your': 'jɔː', 'are': 'ɑː', 'her': 'hɜː',
    'me': 'miː', 'you': 'juː', 'him': 'hɪm', 'us': 'ʌs', 'them': 'ðɛm',
    'can': 'kæn', 'will': 'wɪl', 'must': 'mʌst', 'of': 'ɒv',
}

# US override for the fallback (convert UK strong forms to US)
UK_TO_US_STRONG = {
    'fɔː': 'fɔr', 'wɒz': 'wʌz', 'wɜː': 'wɜr',
    'jɔː': 'jʊr', 'ɑː': 'ɑr', 'hɜː': 'hɜr', 'ɒv': 'ʌv',
}

def apply_weak_forms(ipa: str, dialect: str) -> str:
    """Apply weak‑form reduction to unstressed function words."""
    weak_map = WEAK_UK if (dialect.startswith('en') and 'us' not in dialect) else WEAK_US
    words = ipa.split()
    out = []

    for w in words:
        # ---- Step 1: If it's a plain English word (e.g., "and"), replace with IPA ----
        if re.fullmatch(r'[a-zA-Z]+', w):
            # Get the UK strong form
            strong = ORTHO_TO_IPA_UK.get(w.lower(), w)
            # If US dialect, convert to rhotic equivalents
            if dialect == 'en-us':
                for uk, us in UK_TO_US_STRONG.items():
                    strong = strong.replace(uk, us)
            w = strong

        # ---- Step 2: Apply weak form if there is NO PRIMARY stress ----
        # (secondary stress `ˌ` is ignored – treat as weak)
        if 'ˈ' not in w:
            # Strip all stress marks (primary and secondary) to get bare phonemes
            bare = re.sub(r'[ˈˌ]', '', w)
            # Also strip any trailing punctuation (like . ?) – but we don't have that here
            if bare in weak_map:
                w = weak_map[bare]   # replace the entire word with its weak form

        out.append(w)

    return ' '.join(out)

def main():
    args = sys.argv[1:]
    lang = 'en-gb'          # British by default
    if args:
        if args[0] == '-us':
            lang = 'en-us'
        elif args[0] in ('-uk', '-gb'):
            lang = 'en-gb'
        elif args[0] in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)

    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    try:
        proc = subprocess.run(
            ['phonemize', '-l', lang, '--with-stress'],
            input=text,
            capture_output=True,
            text=True,
            check=True
        )
        raw_ipa = proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'phonemize' command not found. Install phonemizer.", file=sys.stderr)
        sys.exit(1)

    result = apply_weak_forms(raw_ipa, lang)
    print(result)

if __name__ == '__main__':
    main()
