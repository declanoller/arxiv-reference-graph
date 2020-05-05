import fetch_arxiv


start_url = 'https://arxiv.org/abs/1703.07469'
ref_graph = fetch_arxiv.create_reference_graph(start_url, max_depth=2)
