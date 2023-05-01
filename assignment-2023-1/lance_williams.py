import sys
import argparse

#taxinomw tis sustades kai meta tis diatrexw
#ara taxinomisi grafou kai meta anazitisi
#(kata vathos h kata platos?)
#4 periptwseis methodou: single, complete, average, Ward
#aftes aforoun ti metrisi ths apostasis metaksu duo systadwn
#oi systades apotelountai apo stoixeia poy einai omoia metaksy tous
#omoiothta vasi apostasis

method = sys.argv[1]
f = sys.argv[2]

#diavazw to arxeio kai apothikevw to periexomeno se lista
with open (f, 'r') as example: 
    lista = example.read().split()

#kanw tous arithnous sti lista akaireous
lista = [int(num) for num in lista]


#single
def single_linkage(distances, cluster1, cluster2):
    return min(distances[(i, j)] for i in cluster1 for j in cluster2)

#complete
def complete_linkage(distances, cluster1, cluster2):
    return max(distances[(i, j)] for i in cluster1 for j in cluster2)

#average
def average_linkage(distances, cluster1, cluster2):
    distances_sum = sum(distances[(i, j)] for i in cluster1 for j in cluster2)
    avg_distance = distances_sum / (len(cluster1) * len(cluster2))
    return avg_distance

#Ward
def ward_merge(d1, d2, n1, n2):
    return ((n1+n2)/(n1*n2))*d1 + ((n1+n2)/(n1*n2))*d2 - ((n1+n2)/(n1*n2))**2*d1d2


#prwti periptwsi na einai i apli metrisi tis omoiothtas me vasi thn apostasi:Single
if method == 'single':
    print(method)


if method == 'complete':
    print(method)


if method == 'average':
    print(method)


if method == 'Ward':
    print(method)







