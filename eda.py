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

def get_cossim_matrix(tfidf_matrix):
    cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    # #
    # save_file = open("./similarity_matrix_model_v6.csv", mode="w+")
    # np.savetxt('similarity_matrix_model_v6.csv', cosine_sim_matrix, delimiter=',')

    return cosine_sim_matrix


def string_to_vector(df):
    #v1: ngram_range=(1,3)
    tfidf_vectorizer = TfidfVectorizer(ngram_range=(1,1), analyzer='word')
    tfidf_fit = tfidf_vectorizer.fit(df['cleaner_tweet'])
    matrix = tfidf_fit.transform(df['cleaner_tweet'])
    sparse_matrix = sparse.csc_matrix(matrix)
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
        set_trace()
        recs, scores = list(recs), list(scores)
        recs, scores = list(unique_everseen(recs)), list(unique_everseen(scores))
        clean_df.at[i, "top_n_tweets"] = recs
        clean_df.at[i, "top_n_scores"] = scores
    return clean_df


def main():
    clean_df = pd.read_csv('data/clean_tweets_v5.csv')
    tfidf_fit, tfidf_matrix, vocab = string_to_vector(clean_df)
    cosine_sim_matrix = get_cossim_matrix(tfidf_matrix)
    clean_df["top_n_tweets"] = ""

    clean_df['top_n_scores'] = ""

    twitter_series = pd.Series(clean_df.id)

    top_n = 10

    clean_df = generate_results(clean_df, twitter_series, cosine_sim_matrix, top_n+1)

    clean_df.to_csv("data/clean_tweets_v6.csv", index=False)


if __name__ == '__main__':
    main()