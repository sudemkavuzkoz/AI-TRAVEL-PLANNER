from duckduckgo_search import DDGS

def test_ddg():
    with DDGS() as ddgs:
        results = ddgs.text("top 5 famous restaurants in Italy tripadvisor", region='us-en', max_results=5)
        for r in results:
            print("-", r['title'])
            print(" ", r['body'])

if __name__ == "__main__":
    test_ddg()
