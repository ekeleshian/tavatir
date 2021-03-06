import pickle
import string
import re
import sys
import operator
import demoji
import numpy as np
import pandas as pd
import split_hashtags
import time
from nltk.corpus import stopwords
from nltk.tokenize.treebank import TreebankWordTokenizer

import tweet_db
from pdb import set_trace
from collections import defaultdict

with open('data/ht_dict_v4.pkl', 'rb') as file:
    ht_dict = pickle.load(file)

with open('contraction_dict.pkl', 'rb') as file:
    contractions_dict = pickle.load(file)

tokenizer = TreebankWordTokenizer()


def get_text_vocab_coverage(df):
    glove_embeddings = np.load('models/glove.840B.300d.pkl', allow_pickle=True)

    def build_vocab(X):
        tweets = X.apply(lambda s: s.split()).values
        vocab = {}

        for tweet in tweets:
            for word in tweet:
                if vocab.get(word, ''):
                    vocab[word] += 1
                else:
                    vocab[word] = 1
        return vocab

    def check_embeddings_coverage(X, embeddings):
        vocab = build_vocab(X)
        covered = {}
        oov = {}
        n_covered = 0
        n_oov = 0

        for word in vocab:
            try:
                covered[word] = embeddings[word]
                n_covered += vocab[word]
            except:
                oov[word] = vocab[word]
                n_oov += vocab[word]

        vocab_coverage = len(covered) / len(vocab)

        text_coverage = (n_covered / (n_covered + n_oov))

        sorted_oov = sorted(oov.items(), key=operator.itemgetter(1))[::-1]

        return sorted_oov, vocab_coverage, text_coverage

    glove_oov, glove_vocab_coverage, glove_text_coverage = check_embeddings_coverage(
        df['cleaner_tweet'], glove_embeddings)

    return glove_oov, glove_vocab_coverage, glove_text_coverage


def contraction_expander(text):
    text = re.sub(chr(8217), "'", text)
    text = re.sub(chr(8216), "'", text)
    contractions_re = re.compile('(%s)' % '|'.join(contractions_dict.keys()))

    def replace(match):
        return contractions_dict[match.group(0)]

    return contractions_re.sub(replace, text)


def remove_urls(text):
    return re.sub("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", "", text)


def char_entity_references(text):
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&lt;", "<", text)
    return re.sub(r"&amp;", "&", text)


def removeall_punctuations(text):
    text = re.sub(chr(8230), "...", text)
    text = re.sub(chr(8220), '"', text)
    text = re.sub(chr(8221), '"', text)
    text = re.sub(chr(8216), "'", text)
    text = re.sub('~', 'around ', text)

    for p in string.punctuation:
        text = text.replace(p, f' ')

    return text


def replace_emojis(text):
    skin_tones = ["Light Skin Tone", "Medium-Light Skin Tone", "Medium Skin Tone", "Medium-Dark Skin Tone",
                  'Dark Skin Tone']
    skin_tones = [sk.lower() for sk in skin_tones]
    text = demoji.replace_with_desc(text, sep=" ")
    for sk in skin_tones:
        text = re.sub(sk, "", text)
    return text


def removeall_mentions(text):
    return re.sub(r"(^@\w+)|(\s+@\w+)", "", text)


def removeall_hashtags(text):
    return re.sub(r"\W(\#[a-zA-Z]+[0-9]*\b)(?!;)", "", text)


def findall_hashtags(text):
    return re.findall(r"\W(\#[a-zA-Z]+[0-9]*\b)(?!;)", text)


def substitute_hashtags(text):
    hashtags = re.findall(r"\W(\#[a-zA-Z]+[0-9]*\b)(?!;)", text)
    for ht in hashtags:
        ht_ = ht[1:]
        new_ht = split_hashtags.split_hashtag_to_words_all_possibilities(ht_)
        if len(new_ht) > 0:
            new_ht = new_ht[0]
            clean_ht = ' '.join(new_ht)
        else:
            clean_ht = ht_
        text = re.sub(ht, clean_ht, text)
    return text


def substitute_hashtags_v2(row):
    hashtags = row.hashtags
    for ht in hashtags:
        try:
            row.cleaner_tweet = re.sub(ht, ht_dict[ht], row.cleaner_tweet)
        except KeyError as e:
            continue
    return row


def build_hashtag_dict(df):
    all_hts = []

    def concat_hashtags(hts):
        all_hts.extend(hts)

    df['hashtags'].apply(concat_hashtags)
    all_unique_hts = list(set(all_hts))
    ht_dict = dict()
    print("building dictionary...\n")
    for ht in all_unique_hts:
        ht_ = ht[1:]
        new_ht = split_hashtags.split_hashtag_to_words_all_possibilities(ht_)
        if len(new_ht) > 0:
            new_ht = new_ht[0]
            clean_ht = ' '.join(new_ht)
        else:
            clean_ht = ht_

        ht_dict[ht] = clean_ht
    print("saving as pkl file...\n")
    with open('data/ht_dict_v4.pkl', 'wb') as file:
        pickle.dump(ht_dict, file)


def remove_stopwords(text):
    clean_text = text.split(" ")
    clean_text = [word.lower() for word in clean_text if word.lower()
                  not in stopwords.words('english') and word != "RT"]
    return ' '.join(clean_text)


def tokenize_clean_string(clean_tweet):
    return ' '.join(tokenizer.tokenize(clean_tweet))


def expand_vocab_coverage(df):
    df['cleaner_tweet'] = df['content'].apply(remove_urls)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(contraction_expander)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(char_entity_references)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(replace_emojis)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(removeall_mentions)
    df['hashtags'] = df['cleaner_tweet'].apply(findall_hashtags)
    df['is_retweet'] = df['content'].apply(lambda x: "RT" in x[:5])
#     print("created hashtags column and now substitute hashtags\n")
#     start = time.time()
    # df['cleaner_tweet'] = df['cleaner_tweet'].apply(substitute_hashtags)
#     build_hashtag_dict(df)

#     with open('data/ht_dict_v4.pkl', 'rb') as file:
#         ht_dict = pickle.load(file)

    df = df.apply(substitute_hashtags_v2, axis=1)
#     end = time.time()
#     print(f"finished substituting: {str(end-start)} seconds\n")
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(removeall_hashtags)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(removeall_punctuations)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(remove_stopwords)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(tokenize_clean_string)

    glove_oov, glove_vocab_coverage, glove_text_coverage = get_text_vocab_coverage(
        df)

    # print(f"glove vocab coverage without mentions: {glove_vocab_coverage}")
    # print(f"glove text coverage without mentions: {glove_text_coverage}")
    #
    with open("data/glove_oov_v4.pkl", "wb") as file:
        pickle.dump(glove_oov, file)

    return df


def main(n):
    start = time.time()
    df = pd.DataFrame()
    for i in range(1, n+1):
        df = df.append(pd.read_csv(f"data/tavatirTweetsRaw_v{i}.csv"))
    print(f'length of total df: {len(df)}')
    df.drop(columns=["content_id", "matching_rules_ids"], inplace=True)
    df = expand_vocab_coverage(df)
    df.to_csv(f"data/tavatirTweetsProcessed_v4.csv", index=False)
    end = time.time()
    print(f'Time to preprocess: {str(end-start)} seconds\n')


if __name__ == "__main__":
    if len(sys.argv):
        exit("You have to pass in number of raw csv files")
    main(sys.argv[1])
