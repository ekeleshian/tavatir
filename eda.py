from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize.treebank import TreebankWordDetokenizer
import numpy as np
import pandas as pd
from more_itertools import unique_everseen
from scipy import sparse
import pickle
from pdb import set_trace


def detokenize_clean_string(concat_string):
    concat_arr = concat_string.split()
    filtered_arr = TreebankWordDetokenizer().detokenize(concat_arr)
    return filtered_arr

def cosine_similarity_n_space(m1, m2, batch_size=100):
    assert m1.shape[1] == m2.shape[1]
    ret = np.ndarray((m1.shape[0], m2.shape[0]))
    for row_i in range(0, int(m1.shape[0] / batch_size) + 1):
        start = row_i * batch_size
        end = min([(row_i + 1) * batch_size, m1.shape[0]])
        if end <= start:
            break
        rows = m1[start: end]
        sim = cosine_similarity(rows, m2) # rows is O(1) size
        ret[start: end] = sim
    return ret


def string_to_vector(df):
    #v1: ngram_range=(1,3)
    tfidf_vectorizer = TfidfVectorizer(ngram_range=(1,1), analyzer='word')
    tfidf_fit = tfidf_vectorizer.fit(df['cleaner_tweet'])
    matrix = tfidf_fit.transform(df['cleaner_tweet'])
    sparse_matrix = sparse.csr_matrix(matrix)
    vocab = tfidf_vectorizer.vocabulary_

    return tfidf_fit, sparse_matrix, vocab


def get_score_series(tweet_series, tweet_id, cosine_sim):
    idx = tweet_series[tweet_series == tweet_id].index[0]
    return pd.Series(cosine_sim[idx])


def get_topn_tweet_recs(tweet_series, tweet_id, cosine_sim, top_n):
    recs = []
    scores = []
    score_series = get_score_series(tweet_series, tweet_id, cosine_sim)

    if (np.count_nonzero(score_series.values) == 0):
        return recs

    score_series = score_series.sort_values(ascending=False)
    ordered_indices = score_series.index
    i = 0

    while i < top_n:
        curr_tweet_id = tweet_series.iloc[ordered_indices[i]]
        score = score_series.loc[ordered_indices[i]]
        if curr_tweet_id != tweet_id:
            recs.append(curr_tweet_id)
            scores.append(score)
            i += 1
        else:
            i += 1

    return recs, scores


def generate_results(clean_df, tweet_series, cos_sim_matrix, top_n_recs):
    for i in range(len(clean_df)):
        tweet_id = clean_df.iloc[i].id
        recs, scores = get_topn_tweet_recs(tweet_series, tweet_id, cos_sim_matrix, top_n_recs)
        recs, scores = list(recs), list(scores)
#         recs, scores = list(unique_everseen(recs)), list(unique_everseen(scores))
        clean_df.at[i, "top_n_tweets"] = recs
        clean_df.at[i, "top_n_scores"] = scores
    return clean_df


def main():
    clean_df = pd.read_csv('data/tavatirTweetsProcessed_v4.csv')
    tfidf_fit, tfidf_matrix, vocab = string_to_vector(clean_df)
    cosine_sim_matrix = cosine_similarity_n_space(tfidf_matrix, tfidf_matrix)
    clean_df["top_n_tweets"] = ""

    clean_df['top_n_scores'] = ""

    twitter_series = pd.Series(clean_df.id)

    top_n = 10

    clean_df = generate_results(clean_df, twitter_series, cosine_sim_matrix, top_n+1)

    clean_df.to_csv("data/tavatirTweetsPCA_v4.csv", index=False)


if __name__ == '__main__':
    main()