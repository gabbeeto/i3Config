#!/usr/bin/env python3
# smart-phonemize: IPA with weak forms (British by default, -us for American)

import sys
import re
import subprocess

# ---- Weak form dictionaries ----
# American English (rhotic) – includes /r/
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
    'wɒz': 'wəz',   # was
    'wɜr': 'wɚ',    # were
    'jʊr': 'jɚ',    # your
    'ɑr': 'ɚ',      # are
    'hɜr': 'hɚ',    # her
}

# British English (non-rhotic) – no /r/ in weak forms
WEAK_UK = {
    'ænd': 'ənd',   # and
    'fɔː': 'fə',    # for (note: long vowel + no r)
    'tu': 'tə',     # to
    'æt': 'ət',     # at
    'æz': 'əz',     # as
    'ðæt': 'ðət',   # that
    'ðən': 'ðən',   # than
    'ðeə': 'ðə',    # there (centring diphthong + no r)
    'hæz': 'həz',   # has
    'wɒz': 'wəz',   # was
    'wɜː': 'wə',    # were (long vowel + no r)
    'jɔː': 'jə',    # your
    'ɑː': 'ə',      # are
    'hɜː': 'hə',    # her
}

def apply_weak_forms(ipa: str, dialect: str) -> str:
    # Choose the correct map
    if dialect.startswith('en') and 'us' not in dialect:
        # British: 'en' or 'en-gb'
        weak_map = WEAK_UK
    else:
        # American: 'en-us'
        weak_map = WEAK_US

    words = ipa.split()
    out = []
    for w in words:
        # If the word has no primary/secondary stress, it's a function word candidate
        if 'ˈ' not in w and 'ˌ' not in w:
            # Extract only the phonetic core (letters and IPA symbols)
            core = re.sub(r'[^a-zA-Zəɚːɛɔʊɑɒɪʊʌæ]', '', w)
            if core in weak_map:
                w = w.replace(core, weak_map[core])
        out.append(w)
    return ' '.join(out)

def main():
    args = sys.argv[1:]
    # Default: British English
    lang = 'en-gb'
    if args:
        if args[0] == '-us':
            lang = 'en-us'
        elif args[0] in ('-uk', '-gb'):
            lang = 'en'   # explicit British (already default)
        elif args[0] in ('-h', '--help'):
            print("Usage: echo 'text' | smart-phonemize [-us]")
            print("  Default: British English  |  -us : American English")
            sys.exit(0)

    text = sys.stdin.read().strip()
    if not text:
        sys.exit(0)

    # Run the phonemize command
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

    # Apply weak forms with the correct dialect map
    result = apply_weak_forms(raw_ipa, lang)
    print(result)

if __name__ == '__main__':
    main()
