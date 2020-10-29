import pickle
import string
import re
import operator
import demoji
import numpy as np
import pandas as pd
import split_hashtags
import time


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

    glove_oov, glove_vocab_coverage, glove_text_coverage = check_embeddings_coverage(df['cleaner_tweet'], glove_embeddings)

    return glove_oov, glove_vocab_coverage, glove_text_coverage


def expand_vocab_coverage(df):
    with open('contraction_dict.pkl', 'rb') as file:
        contractions_dict = pickle.load(file)

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

    df['cleaner_tweet'] = df['content'].apply(remove_urls)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(contraction_expander)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(char_entity_references)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(replace_emojis)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(removeall_mentions)
    df['hashtags'] = df['cleaner_tweet'].apply(findall_hashtags)
    print("created hashtags column and now substitute hashtags\n")
    start = time.time()
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(substitute_hashtags)
    end = time.time()
    print(f"finished substituting: {str(end-start)} seconds\n")
    # df['cleaner_tweet'] = df['cleaner_tweet'].apply(removeall_hashtags)
    df['cleaner_tweet'] = df['cleaner_tweet'].apply(removeall_punctuations)


    glove_oov, glove_vocab_coverage, glove_text_coverage = get_text_vocab_coverage(df)

    print(f"glove vocab coverage without mentions: {glove_vocab_coverage}")
    print(f"glove text coverage without mentions: {glove_text_coverage}")

    with open("data/glove_oov_v3.pkl", "wb") as file:
        pickle.dump(glove_oov, file)

    return df


if __name__ == "__main__":
    start = time.time()
    df = pd.read_csv("data/tweets_1603925121.csv")
    df.drop(columns=["content_id", "matching_rules_ids", "received_at"], inplace=True)
    df = expand_vocab_coverage(df)
    df.to_csv("data/clean_tweets_v3.csv", index=False)
    end = time.time()
    print(f'Time to preprocess: {str(start-end)} seconds\n')
