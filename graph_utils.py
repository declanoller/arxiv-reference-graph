import os, shutil, re, time, random, json, string
import networkx as nx
import matplotlib.pyplot as plt

import parse_utils as pu
import path_utils


def graph_to_json(g, pos):
	j = {"nodes": [], "links": []}
	y_max = max([pos[node_id][1] for node_id, node_attrs in g.nodes(True)])
	for node_id, node_attrs in g.nodes(True):
		node_attrs['id'] = node_id
		node_attrs['x'] = pos[node_id][0]
		node_attrs['y'] = y_max - pos[node_id][1]
		j["nodes"].append(node_attrs)
	for source, target, attrs in g.edges(data=True):
		j["links"].append({
			"source": source,
			"target": target
		})
	return j



def convert_title_dict_to_graph(title_info_dict):

	print('\nConverting title dict to graph...')

	G = nx.DiGraph()

	N_nodes = len(title_info_dict.keys())

	# Get mapping between ids and node nums and vice versa
	title_nodenum_dict = {k : i for i,k in enumerate(title_info_dict.keys())}
	nodenum_title_dict = {i:k for k,i in title_nodenum_dict.items()}
	nodenum_label_dict = {i:pu.linebreak_every_n_spaces(k, n=2) for i,k in nodenum_title_dict.items()}


	# Add nodes to graph, color map
	node_colors = []
	for k,i in title_nodenum_dict.items():
		node_status = title_info_dict[k]['status']
		if node_status == 'expanded':
			if title_info_dict[k]['refs_source'] == 'from_pdf':
				col = 'plum'
			else:
				col = 'mediumseagreen'
		elif node_status == 'no_id':
			col = 'tomato'
		elif node_status == 'root':
			col = 'orange'
		else:
			col = 'khaki'

		node_colors.append(col)

		node_kwargs = {
			'title' : title_info_dict[k]['title_full'],
			'color' : col,
			'link' : title_info_dict[k]['link'],
			'depth' : title_info_dict[k]['depth'],
            'year' : title_info_dict[k]['year'],
            'n_parents' : title_info_dict[k]['n_parents'],
		}

		G.add_node(i, **node_kwargs)

	# Add edges
	for title, info_dict in title_info_dict.items():

		title_node = title_nodenum_dict[title]

		for c in info_dict['children_titles']:

			child_node = title_nodenum_dict[c]

			G.add_edge(title_node, child_node)


	plt.figure(figsize=(14,8))
	plt.axis('off')
	#nx.draw(G, with_labels=True, font_weight='bold')
	#pos = nx.spring_layout(G)
	pos = nx.nx_agraph.graphviz_layout(G, prog='dot')

	margin = 60
	window_w = 1700
	window_h = 750

	pos_x = [margin + p[0] for p in pos.values()]
	pos_y = [margin + p[1] for p in pos.values()]

	range_x = max(pos_x) - min(pos_x)
	range_y = max(pos_y) - min(pos_y)

	mult_x = window_w/range_x
	mult_y = window_h/range_y

	pos_browser = {i : (p[0]*mult_x, p[1]*mult_y) for i,p in pos.items()}

	graph_fname = 'graph.json'
	if os.path.exists(graph_fname):
		os.remove(graph_fname)

	x = graph_to_json(G, pos_browser)
	print('Writing graph to json file...')
	with open(graph_fname, 'w+') as f:
	    json.dump(x, f, indent=4)


	# Draw network
	nx.draw_networkx_nodes(	G,
							pos,
							nodelist=list(range(N_nodes)),
							node_color=node_colors,
							alpha=0.8,
							edgecolors='black',
							node_size=50)

	#width=1.0,
	nx.draw_networkx_edges(G, pos, alpha=0.5)

	#nx.draw_networkx_labels(G, pos, nodenum_label_dict, font_size=8)


	plt.tight_layout()

	plt.savefig('graph_test.png')
	show_plot = False
	if show_plot:
		plt.show()


































#
