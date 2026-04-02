from upload import process_file
from search import search

# insert document
process_file("sample.pdf")

# query
results = search("What is artificial intelligence?")

for r in results:
    print(r)