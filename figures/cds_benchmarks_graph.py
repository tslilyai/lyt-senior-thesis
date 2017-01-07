#!/usr/bin/python3
import matplotlib.pyplot as plt
import matplotlib.colors as pcolors
from collections import defaultdict
from numpy import median
import numpy as np
import math

TESTS = ["PQRandSingleOps:R","PQRandSingleOps:D","PQPushPop:R",
            "PQPushPop:D", "PQPushOnly:R", "PQPushOnly:D", 
            "Q:PushPop","Q:RandSingleOps", "Q:RandMultiOps",
            "HM1M:F34,I33,E33","HM1M:F90,I5,E5",
            "HM1MMultiOp:F34,I33,E33","HM1MMultiOp:F90,I5,E5",
            "HM125K:F34,I33,E33","HM125K:F90,I5,E5",
            "HM10K:F34,I33,E33","HM10K:F90,I5,E5",
        ]
CONCURRENT_BENCHMARK_FILE = "concurrent/concurrent.data"
FCQUEUES_BENCHMARK_FILE = "fcqueues/fcqueues.data"
HM_BENCHMARK_FILE = "maps/maps_%s.data"
INIT_SIZES = [10000, 100000]
NTHREADS = [1,2,6,12,18]
MEASURES = {
    "speed": " (ops/s)", 
    "aborts": " (%)",
}
QMETRICS = ['speed', 'aborts']
MAPMETRICS = ['speed', 'aborts']
LOADS = [5, 10, 15, 20]

class Plotter():
    def __init__(self):
        self._parse_stats_file()
    

    def _parse_stats_file(self):
        '''
        The data file cds_benchmarks_stats.txt should be parsed into 
        a dictionary with the following format:
           
            the data files are organized with one line per size + number of threads: 
            (queue1 s1, s2, ... : a1, a2...) ; (queue2 s1, s2... : a1, a2...) ;...
            
            test_name {
                size1: [
                    aborts:
                        [data structure data for ds1],
                        [data structure data for ds2],
                        ...
                    speed:
                        [data structure data for ds1],
                        [data structure data for ds2],
                        ...
                ]
                size2: [
                    aborts:
                        [data structure data for ds1],
                        ...
                    speed:
                        [data structure data for ds1],
                        ...
                ]
            }
        ''' 
        def _construct_test_data(filename):
            test_data = defaultdict(dict)
            size_index = 0
            test = ""
            num_ds = 0
            with open(filename, "r") as f:
                for line in f.read().splitlines():
                    if (line == ""):
                        size_index += 1
                        size_index %= len(INIT_SIZES)
                    elif line in TESTS:
                        test = line    
                        size_index = 0
                    else:
                        data = line.split(";")[:-1]
                        if num_ds == 0:
                            num_ds = len(data)

                        if INIT_SIZES[size_index] not in test_data[test]:
                            test_data[test][INIT_SIZES[size_index]] = {
                                    "speed": [[] for _ in range(num_ds)], 
                                    "aborts": [[] for _ in range(num_ds)],
                            }
                       
                        for ds_index in range(num_ds):
                            test_data[test][INIT_SIZES[size_index]]["speed"][ds_index].append(
                                [float(y) for y in (data[ds_index].split(":"))[0].split(",")[:-1]])
                            test_data[test][INIT_SIZES[size_index]]["aborts"][ds_index].append(
                                [float(y) for y in (data[ds_index].split(":"))[1].split(",")[:-1]])
            return test_data

        self.ctests = _construct_test_data(CONCURRENT_BENCHMARK_FILE)
        self.ttests = _construct_test_data(FCQUEUES_BENCHMARK_FILE)
        self.hmtests = {}
        for load in LOADS:
            self.hmtests[load] = _construct_test_data(HM_BENCHMARK_FILE % load)

    def get_pushpop_graphs(self, queues, indices, filename, colors, patterns, results):
        width = 0.5/len(indices)
        qdata = defaultdict(dict)
        for size, data_lists in results.items():
            if len(data_lists['speed'][0]) == 0:
                continue

            for q_index in range(len(queues)):
                qdata[q_index]['speed'] = []
                qdata[q_index]['aborts'] = []
                for i in range(len(data_lists)):
                    qdata[q_index]['speed'].append(data_lists['speed'][q_index][0])
                    qdata[q_index]['aborts'].append(data_lists['aborts'][q_index][0])
        
            for metric in QMETRICS:
                x = range(len(INIT_SIZES)) 
                fig = plt.figure(figsize=(8,7))
                ax = fig.add_subplot(111)
                qbars = []
                for index, data in qdata.items():
                    if index not in indices:
                        continue
                    medians = [median(metrics) for metrics in data[metric]]
                    err_low = [medians[i]-min(metrics) for i,metrics in enumerate(data[metric])]
                    err_high = [max(metrics)-medians[i] for i,metrics in enumerate(data[metric])]
                    qbars.append(ax.bar(x, medians, width, color=colors[index],
                        hatch=patterns[index],
                        yerr=[err_low, err_high], ecolor='black'))
                    x = [v+width for v in x]

                labels = [queues[i] for i in indices]
                if len(labels) < 5:
                    ncols = len(labels)
                    legend = ax.legend(qbars, labels, bbox_to_anchor=(0., 1.02, 1., .1), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
                    ax.set_title("Push-Pop Test %s" % metric, y=1.15)
                else:
                    ncols = int(math.ceil(len(labels)/3.0))
                    ax.set_title("Push-Pop Test %s" % metric, y=1.25)
                    legend = ax.legend(qbars, labels, bbox_to_anchor=(0., 1.02, 1., .2), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
                ax.set_xlabel('Initial Size')
                ax.set_ylabel(metric + MEASURES[metric])
                ax.set_xticks(np.arange(len(INIT_SIZES)) + (len(labels)/2)*width)
                ax.set_xticklabels(INIT_SIZES)
               
                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width, box.height*.85])
                ax.set_xlim(-width, x[len(INIT_SIZES)-1]+ width)
                
                if metric == 'speed':
                    ax.set_ylim(0, 1.2e7)
               
                plt.savefig(filename+"%s%s.png" % ('Q:PushPop', metric))
                #plt.show()
                plt.close()

    def get_randops_graphs(self, ds, indices, filename, colors, patterns, results, testname, metrics, args=None):    
        data = defaultdict(dict)
        for size, data_lists in results.items():
            assert(len(ds) == len(data_lists['speed']))

            for index in range(len(ds)):
                data[index]['speed'] = []
                data[index]['aborts'] = []
                for nthreads_index in range(len(NTHREADS)):
                    data[index]['speed'].append(data_lists['speed'][index][nthreads_index])
                    data[index]['aborts'].append(data_lists['aborts'][index][nthreads_index])

            for metric in metrics:
                fig = plt.figure(figsize=(8,7))
                ax = fig.add_subplot(111)
                for index in range(len(ds)):
                    if index not in indices:
                        continue
                    datum = data[index]
                    medians = [median(mets) for mets in datum[metric]]
                    err_low = [medians[i]-min(mets) for i,mets in enumerate(datum[metric])]
                    err_high = [max(mets)-medians[i] for i,mets in enumerate(datum[metric])]

                    ax.errorbar(NTHREADS, medians, label=ds[index], color=colors[index], 
                            linestyle=patterns[index], linewidth=2, yerr=[err_low, err_high])

                ax.set_xlabel("Number of Threads")
                ax.set_ylabel(metric + MEASURES[metric])

                labels = [ds[i] for i in indices]
                if len(labels) < 5:
                    ax.set_title("Multi-Threaded Singletons Test %s, Initial Size %s" % (metric, size), y=1.15)
                    ncols = len(labels)
                    legend = ax.legend(labels, bbox_to_anchor=(0., 1.02, 1., .1), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
                else:
                    ax.set_title("Multi-Threaded Singletons Test %s, Initial Size %s" % (metric, size), y=1.25)
                    ncols = int(math.ceil(len(labels)/3.0))
                    legend = ax.legend(labels, bbox_to_anchor=(0., 1.02, 1., .2), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})

                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width, box.height*.85])
               
                if 'map' in filename:
                    if metric == 'speed':
                        ax.set_ylim(0, 3e10)
                    ax.set_title("Multi-Threaded Singletons Test %s, Max Load %s" % (metric, args), y=1.15)
                else:
                    if metric == 'speed':
                        ax.set_ylim(0, 1.5e7)
                    elif metric == 'aborts':
                        ax.set_ylim(0, 8)

                ax.set_xlim(0, 20)

                if args != None:
                    plt.savefig(filename+"%s%s%s.png" % (args, testname, metric))
                else:
                    plt.savefig(filename+"%s%d%s.png" % (testname, size, metric))
                #plt.show()
                plt.close()


    def concurrent_queues_graphs(self):
        queues = ["STO1", "STO2", "FCQueueNT", "Basket", "Moir","Michael-Scott","Optimistic","Read-Write","Segmented","TsigasCycle"]
        filename='concurrent/'
        colors = ["red", "red","green"] + [(0.15*i,0.15*i, 0.15*i) for i in range(7)]
        results = self.ctests['Q:PushPop']

        patterns = ['//','','//','', '', '', '', '', '', '']
        self.get_pushpop_graphs(queues, range(len(queues))[1:], filename, colors, patterns, results)

        patterns = ['--','solid','--','solid', 'solid', 'solid', 'solid', 'solid', 'solid', 'solid']
        test_names = ['Q:RandSingleOps']
        for name in test_names:
            results = self.ctests[name]
            self.get_randops_graphs(queues, range(len(queues))[1:], filename, colors, patterns, results, name, QMETRICS)

    def fcqueues_graphs(self):
        queues = ["STO1", "STO2", "FCQueueNT", "Wrapped-FCQueueNT", "STO-FCQueue", "FCQueueWT"]
        stoindices = [0,1]
        ntindices = [2,3]
        tindices = [1,3,4]
        lpindices = [1,3,4,5]

        filename='fcqueues/'
        colors = ["red","red","green","green","purple","blue"]
        results = self.ttests['Q:PushPop']

        # PUSH POP TEST: SPEED 
        patterns = ['//','','//','', '', '']
        self.get_pushpop_graphs(queues, stoindices, filename+"sto", colors, patterns, results)
        self.get_pushpop_graphs(queues, ntindices, filename+"nt", colors, patterns, results)
        self.get_pushpop_graphs(queues, tindices, filename+"t", colors, patterns, results)
        self.get_pushpop_graphs(queues, lpindices, filename+"lp", colors, patterns, results)

        # RAND OPS TEST
        patterns = ['--','solid','--','solid', 'solid', 'solid']
        test_names = ['Q:RandSingleOps']
        for name in test_names:
            results = self.ttests[name]
            self.get_randops_graphs(queues, stoindices, filename+"sto", colors, patterns, results, name, QMETRICS)
            self.get_randops_graphs(queues, ntindices, filename+"nt", colors, patterns, results, name, QMETRICS)
            self.get_randops_graphs(queues, tindices, filename+"t", colors, patterns, results, name, QMETRICS)
            self.get_randops_graphs(queues, lpindices, filename+"lp", colors, patterns, results, name, QMETRICS)

    def hashmaps_graphs(self):
        maps = ["Chaining", "Cuckoo IE", "Cuckoo KF", "CuckooNT"]
        filename='maps/'
        colors = ["red","green","green","blue"]
        patterns = ["solid","--","solid","solid"]
        test_names = [
            "HM1M:F34,I33,E33","HM1M:F90,I5,E5",
            "HM125K:F34,I33,E33","HM125K:F90,I5,E5",
            "HM10K:F34,I33,E33","HM10K:F90,I5,E5",
        ]

        for name in test_names:
            for load in LOADS:
                results = self.hmtests[load][name]
                self.get_randops_graphs(maps, range(len(maps)), filename, colors, patterns, results, name, MAPMETRICS, load)

def main():
    p = Plotter()
    #p.hashmaps_graphs()
    p.fcqueues_graphs()
    p.concurrent_queues_graphs()

if __name__ == "__main__":
    main()
