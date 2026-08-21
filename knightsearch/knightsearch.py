from flask import Flask, render_template, request, redirect
import os
import re
import sqlite3
from urllib.parse import urlparse

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__, template_folder = "./static")

DB_PATH = "/data/crawled_pages.db" if os.path.exists("/data/crawled_pages.db") \
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawled_pages.db")

RECENT_LIMIT = 8
RESULTS_LIMIT = 40
ASSET_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".xml")

# How much a page's link-authority (pagerank) can amplify an already-relevant
# match. Multiplicative rather than additive, so a highly-linked but barely
# matching page can never outrank a genuinely relevant one - it can only
# nudge the ordering among pages that already match the query.
AUTHORITY_WEIGHT = 0.25

# max_df drops terms that show up on almost every page (boilerplate like nav
# links and footers) so they don't dominate every query's score. It has to
# stay high on this corpus: because every Calvin page shares the same site
# nav/footer, ordinary words like "campus" (95% of pages) and "programs"
# (91% of pages) are extremely common without being boilerplate - a lower
# threshold (e.g. the sklearn-typical 0.9) silently deletes them from the
# vocabulary and makes searching for them return zero results.
MAX_DOC_FREQUENCY = 0.95


def domain_of(url):
    return urlparse(url).netloc or url


def canonical_key(url, title):
    return title or url.split('#')[0]


def strip_leading_title(body, title):
    # The crawler's cleaned_content includes the <head><title> text before
    # the visible page content, so a naive snippet often just repeats the
    # title. Skip past that echo so the snippet shows real body text.
    stripped = body.strip()
    title = title.strip()
    if title and stripped.lower().startswith(title.lower()):
        return stripped[len(title):]
    return body


def snippet_for(body, query, radius = 90):
    # Crawled pages carry a lot of nav/breadcrumb boilerplate ahead of the
    # real content, and that boilerplate often contains a stray one-off
    # mention of the query term. Instead of snapping to the first hit,
    # find the window with the most query-term mentions clustered together
    # - that's a much stronger signal of where the page actually talks
    # about the query.
    terms = set(re.findall(r"\w+", query.lower()))
    lower = body.lower()
    positions = sorted(
        idx
        for term in terms
        for idx in (m.start() for m in re.finditer(re.escape(term), lower))
    )

    if not positions:
        snippet = body[:radius * 2]
        return re.sub(r"\s+", " ", snippet).strip() + ("…" if len(body) > radius * 2 else "")

    best_pos, best_count = positions[0], 0
    for p in positions:
        count = sum(1 for q in positions if p - radius <= q <= p + radius)
        if count > best_count:
            best_pos, best_count = p, count

    start = max(0, best_pos - radius)
    end = min(len(body), best_pos + radius)
    snippet = re.sub(r"\s+", " ", body[start:end]).strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(body) else ""
    return prefix + snippet + suffix


class SearchIndex:
    """TF-IDF vector-space index over the crawled corpus.

    Built once at startup so each query costs one sparse matrix-vector
    multiply instead of a full-table LIKE/FTS scan, and results are ranked
    by how well they match the query (relevance) with page-authority
    (pagerank) as a secondary signal - rather than the old approach of
    filtering by a keyword match and sorting purely by pagerank.
    """

    def __init__(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT url, title, cleaned_content, pagerank
            FROM pages
            WHERE cleaned_content IS NOT NULL AND cleaned_content != ''
        """)
        rows = cursor.fetchall()
        conn.close()

        self.urls = [r[0] for r in rows]
        self.titles = [r[1] or "" for r in rows]
        self.bodies = [r[2] or "" for r in rows]
        pageranks = [r[3] or 0.0 for r in rows]

        lo, hi = (min(pageranks), max(pageranks)) if pageranks else (0.0, 0.0)
        span = (hi - lo) or 1.0
        self.pageranks = [(pr - lo) / span for pr in pageranks]

        # Repeat the title into the indexed text so title words count for
        # more than a single mention in the body would.
        documents = [f"{t} {t} {t} {b}" for t, b in zip(self.titles, self.bodies)]

        self.vectorizer = TfidfVectorizer(stop_words = "english", max_df = MAX_DOC_FREQUENCY)
        self.matrix = self.vectorizer.fit_transform(documents) if documents else None

    def search(self, query, limit = RESULTS_LIMIT):
        if self.matrix is None:
            return [], 0

        query_vec = self.vectorizer.transform([query])
        if query_vec.nnz == 0:
            return [], 0

        relevance = cosine_similarity(query_vec, self.matrix).ravel()

        scored = [
            (relevance[i] * (1 + AUTHORITY_WEIGHT * self.pageranks[i]), i)
            for i in range(len(self.urls)) if relevance[i] > 0
        ]
        scored.sort(key = lambda x: x[0], reverse = True)

        results = []
        seen = set()
        for _, i in scored:
            key = canonical_key(self.urls[i], self.titles[i])
            if key in seen:
                continue
            seen.add(key)
            if len(results) < limit:
                body = strip_leading_title(self.bodies[i], self.titles[i])
                results.append((self.urls[i], self.titles[i], snippet_for(body, query)))
        return results, len(seen)


search_index = SearchIndex(DB_PATH)


def get_recent_pages(limit = RECENT_LIMIT):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = " AND ".join(["url NOT LIKE ?"] * len(ASSET_EXTENSIONS))
    cursor.execute(f"""
        SELECT url, title, MAX(id) AS last_id
        FROM pages
        WHERE title IS NOT NULL AND title != ''
        AND {placeholders}
        GROUP BY title
        ORDER BY last_id DESC
        LIMIT ?
    """, [f"%{ext}" for ext in ASSET_EXTENSIONS] + [limit])
    rows = cursor.fetchall()
    conn.close()
    return [{"url": url, "title": title, "domain": domain_of(url)} for url, title, _ in rows]


@app.route("/")
def home():
    return render_template("websearch.html", recent = get_recent_pages())


@app.route("/websearch", methods = ['GET', 'POST'])
def search():
    if request.method != 'POST':
        return redirect('/')

    query = request.form['query'].strip()
    if not query:
        return redirect('/')

    urls, total = search_index.search(query)
    return render_template('results.html', urls = urls, total = total, query = query)


if __name__ == '__main__':
    app.run(debug=False)
