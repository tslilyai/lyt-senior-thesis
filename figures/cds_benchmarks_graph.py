#!/usr/bin/python3
import matplotlib.pyplot as plt
import matplotlib.colors as pcolors
from collections import defaultdict
from numpy import median
import numpy as np

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
INIT_SIZES = [10000, 100000]
NTHREADS = [1,2,6,12,18]
MEASURES = {
    "speed": " (ops/s)", 
    "aborts": " (%)",
}
QMETRICS = ['speed', 'aborts']

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

    def get_pushpop_graphs(self, queues, filename, colors, results):
        width = 0.07
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
            fig = plt.figure(figsize=(8,5))
            ax = fig.add_subplot(111)
            qbars = []
            for index, data in qdata.items():
                medians = [median(speeds) for speeds in data[metric]]
                err_low = [medians[i]-min(speeds) for i,speeds in enumerate(data[metric])]
                err_high = [max(speeds)-medians[i] for i,speeds in enumerate(data[metric])]
                qbars.append(ax.bar(x, medians, width, color=colors[index], yerr=[err_low, err_high], ecolor='black'))
                x = [v+width for v in x]

            legend = ax.legend(qbars, queues, bbox_to_anchor=(0., 1.02, 1., .2), loc="upper center", ncol=3, borderaxespad=0, prop={'size':10})
            ax.set_xlabel('Initial Size')
            ax.set_ylabel(metric + MEASURES[metric])
            ax.set_xticks(np.arange(len(INIT_SIZES)) + 3*width)
            ax.set_xticklabels(INIT_SIZES)
           
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width, box.height*.85])
           
            plt.savefig(filename+"%s%s.png" % ('Q:PushPop', metric))
            plt.show()
            plt.close()

    def get_randops_graphs(self, ds, filename, colors, results, testname, metrics):    
        for size, data_lists in results.items():
            assert(len(ds) == len(data_lists['speed']))

            data = defaultdict(dict)
            for index in range(len(ds)):
                data[index]['speed'] = []
                data[index]['aborts'] = []
                for nthreads_index in range(len(NTHREADS)):
                    data[index]['speed'].append(data_lists['speed'][index][nthreads_index])
                    data[index]['aborts'].append(data_lists['aborts'][index][nthreads_index])

            for metric in metrics:
                fig = plt.figure(figsize=(8,6))
                ax = fig.add_subplot(111)
                for i in range(len(ds)):
                    ax.errorbar(NTHREADS, [median(x) for x in data[i][metric]], label=ds[i], color=colors[i], 
                            yerr=[[median(x)-min(x) for x in data[i][metric]], 
                                [max(x)-median(x) for x in data[i][metric]]])

                ax.set_xlabel("Number of Threads")
                ax.set_ylabel(metric + MEASURES[metric])

                legend = ax.legend(ds, bbox_to_anchor=(0., 1.02, 1., .2), loc="upper center", ncol=3, borderaxespad=0, prop={'size':10})

                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width, box.height*.85])
                
                plt.savefig(filename+"%s%d.png" % (testname, size))
                plt.show()
                plt.close()


    def concurrent_queues_graphs(self):
        queues = ["STO1", "STO2", "FCQueueNT", "Basket", "Moir","Michael-Scott","Optimistic","Read-Write","Segmented","TsigasCycle"]
        filename='concurrent/'
        colors = ["red","red","green", "grey","grey","grey","grey","grey","grey","grey"]
        results = self.ctests['Q:PushPop']

        self.get_pushpop_graphs(queues, filename, colors, results)

        test_names = ['Q:RandSingleOps', 'Q:RandMultiOps']
        for name in test_names:
            results = self.ctests[name]
            self.get_randops_graphs(queues, filename, colors, results, name, QMETRICS)

    def fcqueues_graphs(self):
        queues = ["STO1", "STO2", "FCQueue NT", "Wrapped-FCQueueNT", "FCQueueT", "FCQueueLP"]
        filename='fcqueues/'
        colors = ["red","orange","white","grey","green","blue"]
        results = self.ttests['Q:PushPop']

        # PUSH POP TEST: SPEED 
        self.get_pushpop_graphs(queues, filename, colors, results)

        # RAND OPS TEST
        test_names = ['Q:RandSingleOps', 'Q:RandMultiOps']
        for name in test_names:
            results = self.ttests[name]
            self.get_randops_graphs(queues, filename, colors, results, name, QMETRICS)

def main():
    p = Plotter()
    p.concurrent_queues_graphs()
    p.fcqueues_graphs()

if __name__ == "__main__":
    main()
