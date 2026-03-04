from flask import Flask, render_template, request
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import sqlite3

app = Flask(__name__, template_folder = "./static")

@app.route("/")
def home():
    return render_template("websearch.html")


@app.route("/websearch", methods = ['GET', 'POST'])
def search():#get the query from the requests
    if request.method == 'POST':
        query = request.form['query']
        if query == "":
            return render_template("websearch.html")
        #connect to the db
        conn = sqlite3.connect('/data/crawled_pages.db')
        cursor = conn.cursor()

        #search for websites that match query in their cleaned content
        # cursor.execute("SELECT url, title FROM pages WHERE cleaned_content\
        #                LIKE ? ORDER by pagerank DESC", ('%' + query + '%',))
        cursor.execute("""
            SELECT p.url, p.title 
            FROM pages p
            JOIN pages_fts f ON p.rowid = f.rowid
            WHERE pages_fts MATCH ?
            ORDER BY p.pagerank DESC
        """, (query,))
        urls = cursor.fetchall()

        conn.close()


        return render_template('results.html', urls = urls, query = query)

if __name__ == '__main__':
    app.run(debug=False)
