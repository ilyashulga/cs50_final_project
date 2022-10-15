from cs50 import get_string
import re


def main():
    # Get text input from user in string format
    while True:
        text = get_string('Text: ')
        if len(text) > 0:
            break

    # Find avarage number of letters per 100 words in the text (L)
    L = calculate_L(text)
    # print(L)

    # Find avarage number of sentences per 100 words in the text (S)
    S = calculate_S(text)
    # print(S)

    # Calculate Coleman-Liau index
    # print(0.0588 * L - 0.296 * S - 15.8)
    index = int(round(0.0588 * L - 0.296 * S - 15.8))

    # Check resulting index and print results accordingly
    if index > 16:
        print('Grade 16+')
    elif index < 1:
        print('Before Grade 1')
    else:
        print('Grade %i' % index)
    # print(text)


def calculate_L(text):
    # Calculate characters count using RegEx
    char_count = len(re.findall(r'[a-zA-Z]', text))
    # print(char_count)

    # Calculate words count using RegEx. Substracting all symbols count that are not (a-zA-Z.;!? ,):" - equivalently to substracting all that are "'" in order to do not count words like "Let's" as two words
    word_count = len(re.findall(r'[a-zA-Z]+', text)) - len(re.findall(r'[^(a-zA-Z.;!? ,):"]', text))
    # print(word_count)

    return (char_count/word_count)*100


def calculate_S(text):
    # Calculate words count using RegEx. Substracting all symbols count that are not (a-zA-Z.;!? ,):" - equivalently to substracting all that are "'" in order to do not count words like "Let's" as two words
    word_count = len(re.findall(r'[a-zA-Z]+', text)) - len(re.findall(r'[^(a-zA-Z.;!? ,):"]', text))
    # print(word_count)
    # Calculate sentenses count using RegEx by counting all instanses of .!? in input text
    sent_count = len(re.findall(r'[.!?]', text))
    # print(sent_count)

    return (sent_count/word_count)*100


if __name__ == '__main__':
    main()