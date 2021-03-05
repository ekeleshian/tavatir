from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize.treebank import TreebankWordDetokenizer
import numpy as np
import pandas as pd
from more_itertools import unique_everseen
import plotly.express as px
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
    tweets = list(df['cleaner_tweet'])
    matrix = tfidf_vectorizer.fit_transform(tweets)
    sparse_matrix = sparse.csr_matrix(matrix)
    vocab = tfidf_vectorizer.vocabulary_
    return sparse_matrix, vocab


def get_score_series(tweet_series, tweet_id, cosine_sim):
    idx = tweet_series[tweet_series == tweet_id].index[0]
    return pd.Series(cosine_sim[idx])


def get_topn_tweet_recs(tweet_series, tweet_id, cosine_sim):
    recs = []
    scores = []
    score_series = get_score_series(tweet_series, tweet_id, cosine_sim)

    if (np.count_nonzero(score_series.values) == 0):
        return recs

    score_series = score_series.sort_values(ascending=False)
    ordered_indices = score_series.index
    i = 0
    top_scores_series = score_series[score_series > 0.8]
    tweet_index = list(top_scores_series.index)
    recs = list(tweet_series.iloc[tweet_index].values)
    scores = list(top_scores_series.values)

    try:
        recs.remove(tweet_id)
        scores = scores[1:]
    except:
        print(f"{tweet_id} not in recs")

    return recs, scores


def generate_results(clean_df, tweet_series, cos_sim_matrix, pca_params, tsne_params):
    def reduce_dimensions(df, matrix, kind='pca'):
        if kind != 'tsne':
            pca = PCA(**pca_params, n_components=2)
            print('reducing dimensions with pca....')
            reduced_matrix = pca.fit_transform(matrix)
            df['pca_x'] = reduced_matrix[:, 0]
            df['pca_y'] = reduced_matrix[:, 1]
        tsne = TSNE(**tsne_params, n_components=2)
        print('reducing dimensions with tsne....')
        reduced_matrix = tsne.fit_transform(matrix)
        df['tsne_x'] = reduced_matrix[:, 0]
        df['tsne_y'] = reduced_matrix[:, 1]        

        return df
    
    for i in range(len(clean_df)):
        tweet_id = clean_df.iloc[i].id
        recs, scores = get_topn_tweet_recs(tweet_series, tweet_id, cos_sim_matrix)
        recs, scores = list(recs), list(scores)
        clean_df.at[i, "top_n_tweets"] = recs
        clean_df.at[i, "top_n_scores"] = scores
        
    matrix = []
    
    for idx, row in clean_df.iterrows():
        vector = np.zeros(len(clean_df))
        ids = row.top_n_tweets
        indices = [idx - 1 for idx in ids]
        vector[indices] = 1
        matrix.append(vector)
    
    clean_df = reduce_dimensions(clean_df, matrix, kind='pca')
    
    return clean_df



    

def main(pca_params={'svd_solver': 'auto', 'whiten': False, 'tol': 0.0, 'iterated_power': 'auto'}, 
         tsne_params={'perplexity':30, 'learning_rate': 200, "early_exaggeration": 12.0, "n_iter":1000, "metric": "euclidean",
                      "n_iter_without_progress": 300, "min_grad_norm": 1e-07, "init": "random", "verbose": 0, "method":
                      "barnes_hut", "angle": 0.5, "n_jobs": -1, "square_distances": "legacy"}):
    clean_df = pd.read_csv('data/tavatirTweetsProcessed_v4.csv')
    clean_df = clean_df[~clean_df['cleaner_tweet'].isnull()]
    print(f'remove null tweets {len(clean_df)}')
    clean_df = clean_df.reset_index()
    clean_df['id'] = clean_df.index + 1
    
    tfidf_matrix, vocab = string_to_vector(clean_df)
    
    cosine_sim_matrix = cosine_similarity_n_space(tfidf_matrix, tfidf_matrix)
    
    clean_df["top_n_tweets"] = ""

    clean_df['top_n_scores'] = ""

    twitter_series = pd.Series(clean_df.id)

    clean_df = generate_results(clean_df, twitter_series, cosine_sim_matrix, pca_params, tsne_params)
            
#     clean_df.to_csv("data/tavatirTweetsPCA_v4.csv", index=False)
    clean_df['Khojaly_mentioned'] = clean_df['content'].apply(lambda x: "khojaly" in x.lower())
    
    fig = px.scatter(clean_df, 
                     x='pca_x', 
                     y='pca_y',
                     color="Khojaly_mentioned",
                     hover_data=['cleaner_tweet'],
                     title="clusters from PCA")
    
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            namelength=-1
        )
    )
    
    fig.show()
    
    fig = px.scatter(clean_df, 
                     x='tsne_x', 
                     y='tsne_y',
                     color="Khojaly_mentioned",
                     hover_data=['cleaner_tweet'],
                     title="clusters from TSNE")
    
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            namelength=-1
        )
    )
    
    fig.show()
    
    return clean_df


if __name__ == '__main__':
    main()