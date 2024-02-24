import os
from collections import defaultdict
from pathlib import Path

import nltk
import pymorphy2
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import WordPunctTokenizer


class MainClass:
    BAD_TOKENS_TAGS = {"PREP", "CONJ", "PRCL", "INTJ", "LATN", "PNCT", "NUMB", "ROMN", "UNKN"}

    def __init__(self):
        self.stop_words = set(stopwords.words("russian"))
        self.tokenizer = WordPunctTokenizer()
        self.morph_analyzer = pymorphy2.MorphAnalyzer()
        self.tokens = set()
        self.lemmas = defaultdict(set)

    def run(self, text):
        self.tokens.update(self.tokenizer.tokenize(text))
        self.filter_t()

    def filter_t(self):
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

    def write_t(self, path):
        with open(path, "w") as f:
            f.write("\n".join(self.tokens))

    def write_lemmas(self, path):
        with open(path, "w") as f:
            for token, lemmas in self.lemmas.items():
                f.write(f"{token}: {' '.join(lemmas)}\n")


nltk.download("stopwords")


def html_text(file_path):
    with open(file_path) as f:
        soup = BeautifulSoup(f.read(), features="html.parser")
    return " ".join(soup.stripped_strings)


if __name__ == "__main__":
    mainClass = MainClass()
    pages_texts = []
    directory = '../pages'
    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            pages_texts.append(html_text(file_path))

    mainClass.run(" ".join(pages_texts))
    mainClass.write_t(os.path.join(Path(__file__).parent.resolve(), "tokens.txt"))
    mainClass.write_lemmas(os.path.join(Path(__file__).parent.resolve(), "lemmas.txt"))
