# knightsearch
KnightSearch is a custom-built search engine designed to explore core information retrieval concepts including web crawling, indexing, relevance scoring, and link-based ranking.

Live Deployment:
http://knightsearch.xyz

Overview

KnightSearch crawls and indexes over 1,000 web pages and exposes a query interface that returns ranked results based on a combination of TF-IDF relevance scoring and a simplified PageRank algorithm.

The project was built to understand the internal mechanics of search systems, including document collection, preprocessing, inverted index construction, vector space modeling, and graph-based ranking.

System Architecture
1. Web Crawler

Breadth-first crawling strategy

URL frontier queue with visited set to prevent duplicates

Domain-restricted crawling

HTML parsing using BeautifulSoup

Outgoing link extraction and normalization

Persistent storage of raw and cleaned content

2. Data Storage

SQLite database for document storage

Schema includes:

URL

Raw HTML content

Cleaned text content

Title

Outgoing links

PageRank score

Unique constraints to enforce deduplication

3. Indexing Pipeline

Text preprocessing and cleaning

Inverse (inverted) index construction

TF-IDF vectorization using scikit-learn

Vector space model representation of documents

Query vector transformation using the same trained vectorizer

4. Ranking Strategy

Relevance scoring is computed using:

TF-IDF cosine similarity between query vector and document vectors

PageRank computed via NetworkX over the link graph

Final ranking combines content relevance (term frequency-inverse document frequency) with structural importance (link graph centrality).

5. Backend and Deployment

Backend implemented in Python using Flask

RESTful route handling for query submission and result rendering

Gunicorn used as WSGI server for production

Dependency management via requirements.txt

Public deployment hosted at knightsearch.xyz

Technologies

Python

Flask

SQLite

scikit-learn

NetworkX

Requests

BeautifulSoup

Gunicorn

Concepts Implemented

Web crawling and frontier management

URL normalization and duplicate detection

Inverted indexing

TF-IDF vectorization

Cosine similarity

Link graph modeling

PageRank computation

Query processing pipeline

Production deployment of a Flask application

Purpose

The project was built to gain hands-on experience with the core components of modern search engines and information retrieval systems by implementing each stage manually, from crawling to ranking to deployment.
