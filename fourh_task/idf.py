import math
import os
import shutil
from collections import Counter, defaultdict

import nltk
import pymorphy2
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import WordPunctTokenizer

nltk.download("stopwords")


def get_text_from_html(file_path):
    with open(file_path) as f:
        soup = BeautifulSoup(f.read(), features="html.parser")
    return " ".join(soup.stripped_strings)


def idf_word_counter(files_texts, word):
    count = 0
    for file_name, text in files_texts.items():
        if word in text:
            count += 1
    if count > 100:
        print(word, count)
    return count


class TFIDCalculator:
    BAD_TOKENS_TAGS = {"PREP", "CONJ", "PRCL", "INTJ", "LATN", "PNCT", "NUMB", "ROMN", "UNKN"}

    def __init__(self, text):
        self.text = text
        self.stop_words = set(stopwords.words("russian"))
        self.tokenizer_result = WordPunctTokenizer().tokenize(text)
        self.morph_analyzer = pymorphy2.MorphAnalyzer()
        self.tokens = set()
        self.lemmas = defaultdict(set)
        self.parse_text()

    def parse_text(self):
        self.tokens.update(self.tokenizer_result)
        bad_tokens = set()
        for token in self.tokens:
            morph = self.morph_analyzer.parse(token)
            if (
                any([x for x in self.BAD_TOKENS_TAGS if x in morph[0].tag])
                or token in self.stop_words
            ):
                bad_tokens.add(token)
                continue
            if morph[0].score >= 0.5:
                self.lemmas[morph[0].normal_form].add(token)
        self.tokens = self.tokens - bad_tokens


if __name__ == "__main__":
    try:
        shutil.rmtree("tokens")
        shutil.rmtree("lemmas")
    except FileNotFoundError:
        pass

    files_texts = {}
    for root, _, files in os.walk("../pages"):
        for index, file in enumerate(sorted(files), 1):
            text = get_text_from_html(os.path.join(root, file))
            files_texts[file] = text

    full_text = " ".join(files_texts.values())
    full_text_calc = TFIDCalculator(full_text)
    for file_name, text in files_texts.items():
        text_cals = TFIDCalculator(text)
        words_counter = Counter(text_cals.tokenizer_result)
        os.makedirs("tokens", exist_ok=True)
        for token in text_cals.tokens:
            tf = words_counter[token] / len(text_cals.tokenizer_result)
            idf = math.log(len(files_texts) / idf_word_counter(files_texts, token))
            tf_idf = tf * idf
            new_filename = f"{file_name.split('.')[0]}.txt"
            with open(os.path.join("tokens", new_filename), "a") as f:
                f.write(f"{token} {idf} {tf_idf}\n")
        os.makedirs("lemmas", exist_ok=True)
        for lemma, tokens in text_cals.lemmas.items():
            tf_n = words_counter[lemma]
            for token in tokens:
                tf_n += words_counter[token]
            count = 0
            for text in files_texts.values():
                if any(token in text for token in tokens) or lemma in text:
                    count += 1
            tf = tf_n / len(text_cals.tokenizer_result)
            idf = math.log(len(files_texts) / count)
            tf_idf = tf * idf
            new_filename = f"{file_name.split('.')[0]}.txt"
            with open(os.path.join("lemmas", new_filename), "a") as f:
                f.write(f"{lemma} {idf} {tf_idf}\n")
