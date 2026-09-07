#!/usr/bin/env python3
"""
smart-phonemize: IPA with weak forms + connected speech + dark l + pause markers.
Punctuation inserts " | ". Merges chain across multiple words.
Usage: echo "text" | smart-phonemize [-us] [-uk] [-h]
  Default: British English (en-gb)
  -us  : American English (en-us)
  -uk  : explicit British (same as default)
  -h   : show this help
"""

import sys
import re
import subprocess

# ---- Weak form dictionaries (extended with 'that') -----------------------
WEAK_US = {
    'ænd': 'ənd', 'fɔr': 'fər', 'tu': 'tə', 'æt': 'ət', 'æz': 'əz',
    'ðæt': 'ðət',   # that (conjunction/relative) – weak form
    'ðən': 'ðən', 'ðɛr': 'ðɚ', 'hæz': 'həz',
    'wʌz': 'wəz', 'wɜr': 'wɚ', 'jʊr': 'jɚ', 'ɑr': 'ɚ', 'hɜr': 'hɚ',
    'miː': 'mi', 'juː': 'jə', 'hɪm': 'ɪm', 'ʌs': 'əs',
    'ðɛm': 'ðəm', 'kæn': 'kən', 'wɪl': 'wəl', 'mʌst': 'məst', 'ʌv': 'əv',
}

WEAK_UK = {
    'ænd': 'ənd', 'fɔː': 'fə', 'tu': 'tə', 'æt': 'ət', 'æz': 'əz',
    'ðæt': 'ðət',   # that (weak)
    'ðən': 'ðən', 'ðeə': 'ðə', 'hæz': 'həz',
    'wɒz': 'wəz', 'wɜː': 'wə', 'jɔː': 'jə', 'ɑː': 'ə', 'hɜː': 'hə',
    'miː': 'mi', 'juː': 'jə', 'hɪm': 'ɪm', 'ʌs': 'əs',
    'ðɛm': 'ðəm', 'kæn': 'kən', 'wɪl': 'wəl', 'mʌst': 'məst', 'ɒv': 'əv',
}

# ---- Fallback: orthographic -> strong IPA ---------------------------------
ORTHO_TO_IPA_UK = {
    'and': 'ænd', 'for': 'fɔː', 'to': 'tuː', 'at': 'æt', 'as': 'æz',
    'that': 'ðæt', 'than': 'ðən', 'there': 'ðeə', 'has': 'hæz',
    'was': 'wɒz', 'were': 'wɜː', 'your': 'jɔː', 'are': 'ɑː', 'her': 'hɜː',
    'me': 'miː', 'you': 'juː', 'him': 'hɪm', 'us': 'ʌs', 'them': 'ðɛm',
    'can': 'kæn', 'will': 'wɪl', 'must': 'mʌst', 'of': 'ɒv',
}

UK_TO_US_STRONG = {
    'fɔː': 'fɔr', 'wɒz': 'wʌz', 'wɜː': 'wɜr',
    'jɔː': 'jʊr', 'ɑː': 'ɑr', 'hɜː': 'hɜr', 'ɒv': 'ʌv',
}

# ---- Helper: multi‑character phonemes ------------------------------------
PHONEMES = {'tʃ', 'dʒ', 'ʃ', 'ʒ', 'ŋ', 'ɲ', 'j', 'w', 'h', 'θ', 'ð'}
VOWELS = set('aeiouəɑɒɔɛɪʊ')

def is_vowel(phoneme):
    if not phoneme:
        return False
    return phoneme[0] in VOWELS or phoneme in ('ə', 'ɑː', 'ɜː', 'eə', 'ɪə', 'ʊə')

def get_first_phoneme(word):
    stripped = re.sub(r'^[ˈˌ]+', '', word)
    if not stripped:
        return '', 0
    for ph in PHONEMES:
        if stripped.startswith(ph):
            return ph, len(word) - len(stripped) + len(ph)
    return stripped[0], len(word) - len(stripped) + 1

def get_last_phoneme(word):
    stripped = re.sub(r'[ˈˌ]+$', '', word)
    if not stripped:
        return '', 0
    for ph in PHONEMES:
        if stripped.endswith(ph):
            start = len(word) - len(stripped) + (len(stripped) - len(ph))
            return ph, start
    return stripped[-1], len(word) - len(stripped) + len(stripped) - 1

def replace_last_phoneme(word, new_ph):
    ph, start = get_last_phoneme(word)
    if not ph:
        return word
    return word[:start] + new_ph

def replace_first_phoneme(word, new_ph):
    ph, end = get_first_phoneme(word)
    if not ph:
        return word
    stress_prefix = re.match(r'^[ˈˌ]*', word).group(0)
    after = word[len(stress_prefix)+len(ph):]
    return stress_prefix + new_ph + after

def remove_first_phoneme(word):
    ph, end = get_first_phoneme(word)
    if not ph:
        return word
    stress_prefix = re.match(r'^[ˈˌ]*', word).group(0)
    after = word[len(stress_prefix)+len(ph):]
    return stress_prefix + after

# ---- Connected speech (with chaining merges) ----------------------------
def apply_connected_speech(ipa: str, dialect: str) -> str:
    words = ipa.split()
    if len(words) < 2:
        return ipa

    is_rhotic = (dialect == 'en-us')
    merged = []
    i = 0
    while i < len(words):
        # Start a new cluster with the current word
        current = words[i]
        i += 1
        # Try to merge with following words
        while i < len(words):
            next_word = words[i]
            last_ph, _ = get_last_phoneme(current)
            first_ph, _ = get_first_phoneme(next_word)
            modified_current = current
            modified_next = next_word
            should_merge = False

            if last_ph and first_ph:
                # Bilabialization
                if first_ph in 'pbm':
                    if last_ph in 'nŋ':
                        modified_current = replace_last_phoneme(modified_current, 'm')
                    elif last_ph == 't':
                        modified_current = replace_last_phoneme(modified_current, 'p')
                    elif last_ph == 'd':
                        modified_current = replace_last_phoneme(modified_current, 'b')
                    elif last_ph == 'j':
                        modified_current = replace_last_phoneme(modified_current, 'b')
                # Alveolarization
                elif first_ph in 'tdn' and last_ph == 'ɲ':
                    modified_current = replace_last_phoneme(modified_current, 'n')
                # Palato-alveolarization
                elif last_ph == 'd' and first_ph == 'j':
                    modified_current = replace_last_phoneme(modified_current, 'dʒ')
                    modified_next = remove_first_phoneme(modified_next)
                    should_merge = True
                elif last_ph == 't' and first_ph == 'j':
                    modified_current = replace_last_phoneme(modified_current, 'tʃ')
                    modified_next = remove_first_phoneme(modified_next)
                    should_merge = True
                elif last_ph == 's' and first_ph in 'ʃtʃdʒj':
                    modified_current = replace_last_phoneme(modified_current, 'ʃ')
                elif last_ph == 'z' and first_ph in 'ʃtʃj':
                    modified_current = replace_last_phoneme(modified_current, 'ʒ')
                # Velarization
                elif first_ph in 'kg':
                    if last_ph == 't':
                        modified_current = replace_last_phoneme(modified_current, 'k')
                    elif last_ph == 'd':
                        modified_current = replace_last_phoneme(modified_current, 'g')
                    elif last_ph == 'n':
                        modified_current = replace_last_phoneme(modified_current, 'ŋ')

                # Linking R (non‑rhotic)
                if not is_rhotic:
                    non_rhotic_vowels = ('ə', 'ɑː', 'ɜː', 'eə', 'ɪə', 'ʊə')
                    last_mod, _ = get_last_phoneme(modified_current)
                    if last_mod in non_rhotic_vowels:
                        first_mod, _ = get_first_phoneme(modified_next)
                        if first_mod and is_vowel(first_mod):
                            modified_current = modified_current + 'r'
                            should_merge = True

                # Gemination
                last_mod, _ = get_last_phoneme(modified_current)
                first_mod, _ = get_first_phoneme(modified_next)
                if last_mod and first_mod and last_mod == first_mod:
                    modified_next = remove_first_phoneme(modified_next)
                    should_merge = True

                # Consonant‑vowel linking
                last_mod, _ = get_last_phoneme(modified_current)
                first_mod, _ = get_first_phoneme(modified_next)
                if last_mod and first_mod:
                    if not is_vowel(last_mod) and is_vowel(first_mod):
                        should_merge = True

            if should_merge:
                # Merge: strip leading stress from next, combine
                next_stripped = re.sub(r'^[ˈˌ]+', '', modified_next)
                current = modified_current + next_stripped
                i += 1  # consume the next word
            else:
                # No more merges, break out of inner loop
                break
        # Append the accumulated (possibly merged) word
        merged.append(current)
    return ' '.join(merged)

# ---- Dark L --------------------------------------------------------------
def apply_dark_l(ipa: str) -> str:
    result_words = []
    for word in ipa.split():
        new_word = []
        i = 0
        while i < len(word):
            ch = word[i]
            if ch == 'l':
                j = i + 1
                while j < len(word) and word[j] in 'ˈˌ':
                    j += 1
                if j < len(word):
                    next_char = word[j]
                    if is_vowel(next_char):
                        new_word.append(ch)
                    else:
                        new_word.append('ɫ')
                else:
                    new_word.append('ɫ')
            else:
                new_word.append(ch)
            i += 1
        result_words.append(''.join(new_word))
    return ' '.join(result_words)

# ---- Process a single text chunk -----------------------------------------
def process_chunk(text: str, dialect: str) -> str:
    if not text.strip():
        return ""

    try:
        proc = subprocess.run(
            ['phonemize', '-l', dialect, '--with-stress'],
            input=text.strip(),
            capture_output=True,
            text=True,
            check=True
        )
        raw_ipa = proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'phonemize' command not found.", file=sys.stderr)
        sys.exit(1)

    # Weak forms
    weak_map = WEAK_UK if (dialect.startswith('en') and 'us' not in dialect) else WEAK_US
    words = raw_ipa.split()
    out = []
    for w in words:
        if re.fullmatch(r'[a-zA-Z]+', w):
            strong = ORTHO_TO_IPA_UK.get(w.lower(), w)
            if dialect == 'en-us':
                for uk, us in UK_TO_US_STRONG.items():
                    strong = strong.replace(uk, us)
            w = strong
        if 'ˈ' not in w:
            bare = re.sub(r'[ˈˌ]', '', w)
            if bare in weak_map:
                w = weak_map[bare]
        out.append(w)

    result = ' '.join(out)
    result = apply_connected_speech(result, dialect)
    result = apply_dark_l(result)
    return result

# ---- Main with pause markers --------------------------------------------
def main():
    args = sys.argv[1:]
    lang = 'en-gb'
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

    # Split on punctuation (.,;:!?) followed by optional whitespace
    chunks = re.split(r'[.,;:!?]+[\s]*', text)
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

    processed = []
    for chunk in chunks:
        ipa = process_chunk(chunk, lang)
        if ipa:
            processed.append(ipa)

    output = ' | '.join(processed)
    print(output)

if __name__ == '__main__':
    main()
