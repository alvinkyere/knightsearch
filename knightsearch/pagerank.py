import sqlite3
import networkx as nx

#connect through sqlite connection
conn = sqlite3.connect('crawled_pages.db')
cursor = conn.cursor()

#retieve urls in all websites 
cursor.execute('SELECT url FROM pages')
urls = [ row[0] for row in cursor.fetchall()]

#create a empty directed graph usin nx
graph = nx.DiGraph()
for url in urls:
    graph.add_node(url)


#get outgoing link of each website from the db
for url in urls:
    cursor.execute('SELECT outgoing_links FROM pages WHERE url = ?', (url,))
    outgoing_links = cursor.fetchone()[0].split(',')
    for link in outgoing_links:
        if link.startswith('http'):
            graph.add_edge(url,link)


#calculate pagerank of the graph
pagerank = nx.pagerank(graph)

#store pg in db
for url in urls:
    cursor.execute("UPDATE pages SET pagerank = ? WHERE url = ?",
                   (pagerank[url], url))
conn.commit()
conn.close()