import streamlit as st
import pandas as pd
from surprise import Reader, Dataset
from joblib import load
# import numpy as np

page_bg_img = """
<style>
[data-testid="stAppViewContainer"]{
    background-color: #508C9B;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# Load data
Ratings = pd.read_csv('Ratings.csv')
Books = pd.read_csv('DataGabungan.csv')
Ratings.rename(columns={"User-ID": "user_id", "Book-Rating": "rating"}, inplace=True)
Ratings = Ratings[Ratings['rating'] != 0]

# Filter data
counters = Ratings.groupby('ISBN')['user_id'].nunique().reset_index(name='user_count')
book_filter = counters[counters['user_count'] >= 40]['ISBN']
user_filter = Ratings.groupby('user_id').size() >= 30
Ratings = Ratings[Ratings['user_id'].isin(user_filter[user_filter].index) & Ratings['ISBN'].isin(book_filter)]
Books.drop(['Unnamed: 0', 'user_id', 'rating'], axis=1, inplace=True)

# Load the full dataset
reader = Reader(rating_scale=(1, 10))
data = Dataset.load_from_df(Ratings, reader)

def book_read(user_id):
    books_list = list(Books['ISBN'])
    book_read_list = list(Ratings['ISBN'][Ratings['user_id'] == user_id])
    return books_list, book_read_list

# Load models
npred = load('npred_model.joblib')
knn = load('knn_model.joblib')
svd = load('svd_model.joblib')
svdpp = load('svdpp_model.joblib')

st.sidebar.title("Menu")
options = st.sidebar.radio("Go to", ['Top 20 Books', 'Recommend a Book'])

def get_recommendation(model, user_id, n=5):
    all_books, user_books = book_read(user_id)
    next_books = [book for book in all_books if book not in user_books]

    if n <= len(next_books):
        ratings = []
        for book in next_books:
            est = model.predict(user_id, book).est
            ratings.append((book, est))
        ratings = sorted(ratings, key=lambda x: x[1], reverse=True)
        book_ids = [id for id, rate in ratings[:n]]
        recommend_books = Books[Books.ISBN.isin(book_ids)][['ISBN', 'title', 'author', 'year', 'average_rating', 'count_ratings', 'predicted_ratings', 'image']]
        recommend_books['average_rating'] = recommend_books['average_rating'].round(2)
        recommend_books['predicted_rating'] = [rate for _, rate in ratings[:n]]
         
        return recommend_books
    else:
        st.write('Please reduce your recommendation request')
        return
# def get_recommendation(model, user_id, n=5):
#     all_books, user_books = book_read(user_id)
#     next_books = [book for book in all_books if book not in user_books]

#     if n <= len(next_books):
#         ratings = []
#         for book in next_books:
#             est = model.predict(user_id, book).est
#             ratings.append((book, est))
#         ratings = sorted(ratings, key=lambda x: x[1], reverse=True)
        
#         # Select top n books based on predicted rating
#         top_ratings = ratings[:n]
#         book_ids = [id for id, rate in top_ratings]
        
#         # Retrieve books in the same order as the predicted ratings
#         recommend_books = Books[Books.ISBN.isin(book_ids)].set_index('ISBN').loc[book_ids].reset_index()
#         recommend_books['average_rating'] = recommend_books['average_rating'].round(2)
#         recommend_books['predicted_rating'] = [rate for _, rate in top_ratings]
         
#         return recommend_books
#     else:
#         st.write('Please reduce your recommendation request')
#         return

def get_top_20_books():
    top_books = Books.sort_values(by='average_rating', ascending=False).head(20)
    top_books['average_rating'] = top_books['average_rating'].round(2)
    return top_books[['ISBN', 'title', 'author', 'year', 'average_rating', 'count_ratings', 'image']]

def display_books(books):
    for _, row in books.iterrows():
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); padding: 10px; border-radius: 10px; background-color: #134B70;">
            <img src="{row['image']}" alt="{row['title']}" style="width: 100px; height: 150px; margin-right: 20px; border-radius: 5px;">
            <div>
                <h4 style="margin: 0; padding: 0;">{row['title']}</h4>
                <p style="margin: 0; padding: 0;"><b>Author:</b> {row['author']}</p>
                <p style="margin: 0; padding: 0;"><b>Year:</b> {row['year']}</p>
                 <p style="margin: 0; padding: 0;"><b>ISBN:</b> {row['ISBN']}</p>
                <p style="margin: 0; padding: 0;"><b>Average Rating:</b> {row['average_rating']}</p>
                <p style="margin: 0; padding: 0;"><b>Number of Ratings:</b> {row['count_ratings']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


# Streamlit UI

if options == 'Top 20 Books':
    st.title('Top 20 Recommended Books')
    top_books = get_top_20_books()
    display_books(top_books)

elif options == 'Recommend a Book':
    st.title('Book Recommendation System')
    user_id = st.number_input('Enter User ID', min_value=0)
    method = st.selectbox('Select Recommendation Method', ('NormalPredictor', 'KNN', 'SVD', 'SVD++'))
    n_recommendations = st.slider('Number of Recommendations', min_value=1, max_value=10, value=5)

    st.markdown("""
    <style>
    .stButton > button {
        display: block;
        margin: 0 auto;
        background-color: green;
        color: white;
    }
                
    .stButton > button:hover {
        color: black;
        border: 2px solid green;
        box-shadow: 0 8px 20px 0 rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button('Get Recommendations'):
        if method == 'NormalPredictor':
            recommendations = get_recommendation(npred, user_id, n_recommendations)
        elif method == 'KNN':
            recommendations = get_recommendation(knn, user_id, n_recommendations)
        elif method == 'SVD':
            recommendations = get_recommendation(svd, user_id, n_recommendations)
        elif method == 'SVD++':
            recommendations = get_recommendation(svdpp, user_id, n_recommendations)
        
        if recommendations is not None:
            display_books(recommendations)
