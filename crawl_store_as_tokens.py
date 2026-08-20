import pickle
import os
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import requests
import warnings
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk


warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def save_tokenized_text(tokenized_text, filename):
    with open(filename, 'wb') as f:
        pickle.dump(tokenized_text, f)


if not os.path.exists('tokenized_text_pickle.pkl'):
    websites = ['http://calvin.edu']
    text_content = []
    for website in websites:
        response = requests.get(website)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content.append(soup.get_text())


    stop_words = ['the', 'to', 'an']
    # words = word_tokenize(text_content)

    tokenized_text = []
    for content in text_content:
        tokens = content.lower().split()
        tokenized_text.append([token for token in tokens if token not in stop_words])

    save_tokenized_text(tokenized_text, 'tokenized_text_pickle.pkl')