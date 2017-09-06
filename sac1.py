from igraph import *
import pandas as pd
import sys, itertools, copy, math, csv
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import time

# Function to calculate the similarity matrix using cosine similarity measure
def similarity_matrix():
	similarity_matrix = [[0]*len(attributes_data)]*len(attributes_data)
	for i in range(len(attributes_data)):
		for j in range(len(attributes_data)):
			similarity_matrix[i][j]=cosine_similarity(attributes_data[i],attributes_data[j])[0][0]
	return similarity_matrix

# Function to calculate similarity matrix between new communities 
def latest_similarity_matrix(communities):
	similarity_matrix = [[0]*len(communities)]*len(communities)
	for i in range(len(communities)):
		for j in range(len((communities))):
			summation = 0
			for m in communities[i]:
				for n in communities[j]:
					summation = summation + duplicate_similarity_matrix[m][n]
			similarity_matrix[i][j] = summation
	return similarity_matrix

# Function to re-number nodes from 0 
def renumerate(membership):
	temp_dict = {}
	membership1 = []
	count = 0 
	for i in membership:
		if i in temp_dict.keys():
			membership1.append(temp_dict[i])
		else:
			membership1.append(count);
			temp_dict[i] = count
			count = count + 1
	return membership1

# Function to identify nodes belonging to the same cluster
def phase1(membership, iterations):
	
	vertices = len(set(membership))

	for k in range(iterations):
		for i in range(vertices):

			max_gain = 0.0
			node_max = -1
			node_temp = membership[i]

			QN_delta = 0.0
			QA_delta = 0.0

			QN_original = g.modularity(membership)

			for j in range(vertices):

				if (j == i or membership[i] == membership[j]):
					continue

				membership[i] = membership[j]

				QN_new = g.modularity(membership)
				QN_delta = QN_new - QN_original

				l = 0
				for k in membership:
					if(k == membership[j]):
						l = l + 1

				for vertex, vertex_new in enumerate(membership):
					if(vertex_new == membership[j]):
						QA_delta += similarity_matrix[i][vertex]

				QA_delta = QA_delta / (l*l)

				Q_delta = (alpha * QN_delta) + ((1 - alpha) * QA_delta)

				if Q_delta > max_gain:
					max_gain = Q_delta
					node_max = j

				membership[i] = node_temp

			if max_gain > 0 and node_max != -1:
				membership[i] = membership[node_max]
	
	return membership

# Function to obtain communities and generate new graph with these communities
def phase2(communities, membership):

	print membership
	membership = renumerate(membership)
	print membership
	g.contract_vertices(membership)
	g.simplify(multiple=True)

	communities_new = list(Clustering(membership))
	update_communities = []
	for i in communities_new:
		temp = []
		for j in i:
			temp = temp + communities[j]
		update_communities.append(temp)
	communities = update_communities
	print communities
	similarity_matrix = latest_similarity_matrix(communities)
	membership=[x for x in range(g.vcount())]

	return membership, communities


if __name__ == '__main__':

	# Capture input from the user
	if len(sys.argv) != 2:
		print "Error! Type: python <filename> <alpha_value>"
		sys.exit(1)

	# Store the start time
	start_time = time.time()

	# Capture the alpha value given as input
	alpha = float(sys.argv[1])
	
	# Read the edges and generate graph
	g = Graph.Read_Edgelist('/data/fb_caltech_small_edgelist.txt')
	
	# Read the attributes of the graph
	with open('/data/fb_caltech_small_attrlist.csv') as attr_list:
		reader = csv.reader(attr_list)
		attributes_data = list(reader)[1:]

	# Initialize edge weight to 1
	for edge in g.es():
		edge['weight'] = 1

	# Attach corresponding attributes to edges
	g.get_edgelist()[0:10]
	for i in range(324):
		g.vs[i]["attr"] = attributes_data[i]

	# Compute initial similarity matrix
	similarity_matrix = similarity_matrix()
	duplicate_similarity_matrix = similarity_matrix

	# Obtain memebership of each vertex and create initial communities
	membership = [x for x in range(g.vcount())]
	communities = list(Clustering(membership))

	# Call phase1 and phase2 to obtain membership and communities
	membership = phase1(membership, 2)
	membership, communities = phase2(communities, membership)
	membership = phase1(membership, 2)

	# Obtain the final membership and remove any empty lists
	membership_1 = renumerate(membership)
	membership_final = [x for x in membership_1 if x != []]
	
	# Obtain the final updated communities
	communities_final = list(Clustering(membership_final))
	update_communities = []
	for i in communities_final:
		temp = []
		for j in i:
			temp = temp + communities[j]
		update_communities.append(temp)
	communities_final = update_communities

	# Display the final membership, final communities, and computation time
	#print "Membership: ", membership_final
	#print "Communities: ", communities_final
	#print ("--- %s seconds ---" % (time.time() - start_time))

	# Depending on alpha value, save communities to file
	if alpha == 0:
		f = open("communities_0.txt", "w")
	if alpha == 0.5:
		f = open("communities_5.txt", "w")
	if alpha == 1:
		f = open("communities_1.txt", "w")
	for line in communities_final:
		f.write(", ".join(str(x) for x in line))
		f.write("\n")
	f.close()
