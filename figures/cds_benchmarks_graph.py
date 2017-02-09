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
NTHREADS = [1,2,4,8,12,16,20]
MEASURES = {
    "speed": " (ops/s)", 
    "aborts": " (%)",
}
fullnesses = [5, 10, 15]#, 20]

#run with 10000000 transactions per thread
#perf catches every 1000th cache miss
#fullness of 5
#put in bar graphs
map_cache_misses_5 = {
    "T-Chaining":[205,334,422],
    "T-CuckooKF":[250,418,495],
    "T-CuckooIE":[253,645,735],
    "NT-Cuckoo": [115,200,289],
}
map_cache_misses_10 = {
    "T-Chaining":[229,546,660],
    "T-CuckooKF":[273,464,545],
    "T-CuckooIE":[294,931,969],
    "NT-Cuckoo": [107,191,252],
}
map_cache_misses_15 = {
    "T-Chaining":[260,711,886],
    "T-CuckooKF":[298,527,609],
    "T-CuckooIE":[348,1000,1000],
    "NT-Cuckoo": [138,225,301],
}
map_cache_misses_5_90 = {
    "T-Chaining":[37,197,300],
    "T-CuckooKF":[52,284,359],
    "T-CuckooIE":[53,509,484],
    "NT-Cuckoo": [28,113,226],
}
map_cache_misses_10_90 = {
    "T-Chaining":[40,433,513],
    "T-CuckooKF":[60,347,443],
    "T-CuckooIE":[61,772,761],
    "NT-Cuckoo": [31,152,246],
}
map_cache_misses_15_90 = {
    "T-Chaining":[48,677,740],
    "T-CuckooKF":[72,409,537],
    "T-CuckooIE":[98,1000,1000],
    "NT-Cuckoo": [34,171,304],
}
queue_cache_misses = {
    "WT-FCQueue" : [299],
    "T-FCQueue": [765],
    "NT-FCQueue": [157],
    "NT-FCQueueWrapped": [173],
    "WT-Queue": [477],
    "T-Queue1": [232],
    "T-Queue2": [184],
}

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
        for fullness in fullnesses:
            self.hmtests[fullness] = _construct_test_data(HM_BENCHMARK_FILE % fullness)

    def get_cm_graphs(self, ds, colors, patterns, filename, cm_map, args=None):
        width = 0.5/len(ds)
        fig = plt.figure(figsize=(7,5))
        ax = fig.add_subplot(111)
        bars = []
        labels = []
        num_entries = (len(list(cm_map.values())[0]))
        x = range(num_entries)

        if num_entries == 1:
            order = [0,1,6,2,3,4,5]
        else:
            order = range(len(ds))
        for i in order:
            labels.append(ds[i])
            bars.append(ax.bar(x, cm_map[ds[i]], width, color=colors[i], hatch=patterns[i]))
            x = [v+width for v in x]
        
        if len(ds) < 5:
            ncols = len(ds)
            legend = ax.legend(bars, labels, bbox_to_anchor=(0., 1.0, 1., 0.2), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
        else:
            ncols = int(math.ceil(len(ds)/3.0))
            legend = ax.legend(bars, labels, bbox_to_anchor=(0., 1.0, 1., .3), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
       
        ax.set_ylabel("Cache Misses (Thousands)")
        if len(x) > 1:
            ax.set_xlabel('Number of Buckets')
            ax.set_xticks(np.arange(3) + (len(ds)/2)*width)
            ax.set_xticklabels(["10K", "125K", "1M"])
        else:
            plt.tick_params(axis='x',which='both',bottom='off',top='off',labelbottom='off')
       
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width, box.height*0.85])
        ax.set_xlim(-width, x[num_entries-1]+ width)
        ax.set_ylim(0, 1000)
       
        if args:
            plt.savefig(filename+str(args)+"cm.png")
        else:
            plt.savefig(filename+"cm.png")
        #plt.show()
        plt.close()


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
       
            x = range(len(INIT_SIZES)) 
            fig = plt.figure(figsize=(8,7))
            ax = fig.add_subplot(111)
            qbars = []
            for index in indices:
                data = qdata[index]
                medians = [median(metrics) for metrics in data['speed']]
                err_low = [medians[i]-min(metrics) for i,metrics in enumerate(data['speed'])]
                err_high = [max(metrics)-medians[i] for i,metrics in enumerate(data['speed'])]
                qbars.append(ax.bar(x, medians, width, color=colors[index],
                    hatch=patterns[index],
                    yerr=[err_low, err_high], ecolor='black'))
                x = [v+width for v in x]

            labels = [queues[i] for i in indices]
            if len(labels) < 5:
                ncols = len(labels)
                legend = ax.legend(qbars, labels, bbox_to_anchor=(0., 1.02, 1., .1), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
            else:
                ncols = int(math.ceil(len(labels)/3.0))
                legend = ax.legend(qbars, labels, bbox_to_anchor=(0., 1.02, 1., .2), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
            ax.set_xlabel('Initial Size')
            ax.set_ylabel("Speed" + MEASURES['speed'])
            ax.set_xticks(np.arange(len(INIT_SIZES)) + (len(labels)/2)*width)
            ax.set_xticklabels(INIT_SIZES)
           
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width, box.height*.85])
            ax.set_xlim(-width, x[len(INIT_SIZES)-1]+ width)
            ax.set_ylim(0, 1.2e7)
           
            plt.savefig(filename+"%s.png" % ('Q:PushPop'))
            #plt.show()
            plt.close()

            # aborts
            begin_lines = [
                '\\begin{tabular}{|c|c|c|}',
                '\\hline',
                '\\multirow{2}{*}{Queue} & \\multicolumn{2}{c|}{Initial Size Abort Rate (\%)}\\\\'
                '\\cline{2-3}'
                '& \qquad 10000 \qquad\quad & 100000\\\\',
            ]
            end_lines = [
                '\\hline'
                '\\end{tabular}',
            ]

            with open(filename+'pushpop_aborts.tex', 'w') as f:
                for line in begin_lines:
                    f.write(line+"\n")
                f.write('\\hline'+"\n")
                f.write('\\hline'+"\n")
                for i in indices:
                    data = qdata[i]['aborts']
                    f.write(queues[i] + ' & ' 
                            + '{0:.3f}'.format(median(data[0])) + ' & ' 
                            + '{0:.3f}'.format(median(data[1])) + '\\\\\n' 
                    )
                for line in end_lines:
                    f.write(line + '\n')

    def get_randops_graphs(self, ds, indices, filename, colors, patterns, results, testname, args=None):    
        data = defaultdict(dict)
        for size, data_lists in results.items():
            assert(len(ds) == len(data_lists['speed']))

            for index in range(len(ds)):
                data[index]['speed'] = []
                data[index]['aborts'] = []
                for nthreads_index in range(len(NTHREADS)):
                    data[index]['speed'].append(data_lists['speed'][index][nthreads_index])
                    data[index]['aborts'].append(data_lists['aborts'][index][nthreads_index])

            fig = plt.figure(figsize=(8,7))
            ax = fig.add_subplot(111)
            for index in indices:
                datum = data[index]
                medians = [median(mets) for mets in datum['speed']]
                err_low = [medians[i]-min(mets) for i,mets in enumerate(datum['speed'])]
                err_high = [max(mets)-medians[i] for i,mets in enumerate(datum['speed'])]

                ax.errorbar(NTHREADS, medians, label=ds[index], color=colors[index], 
                        linestyle=patterns[index], linewidth=2, yerr=[err_low, err_high])

            ax.set_xlabel("Number of Threads")
            ax.set_ylabel("Speed" + MEASURES['speed'])

            labels = [ds[i] for i in indices]
            if len(labels) < 5:
                ax.set_title("Initial Size %s" % (size), y=1.15)
                ncols = len(labels)
                legend = ax.legend(labels, bbox_to_anchor=(0., 1.02, 1., .1), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})
            else:
                ax.set_title("Initial Size %s" % (size), y=1.25)
                ncols = int(math.ceil(len(labels)/3.0))
                legend = ax.legend(labels, bbox_to_anchor=(0., 1.02, 1., .2), loc="upper center", ncol=ncols, borderaxespad=0, prop={'size':11})

            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width, box.height*.85])
           
            if 'map' in filename:
                ax.set_ylim(0, 1.2e8)
                ax.set_title("Max Fullness %s" % (args), y=1.15)
            else:
                ax.set_ylim(0, 2e7)
            ax.set_xlim(0, 21)

            if args != None:
                plt.savefig(filename+"%s%s.png" % (args, testname))
            else:
                plt.savefig(filename+"%s%d.png" % (testname, size))
            #plt.show()
            plt.close()

            # aborts
            if 'map' not in filename:
                begin_lines = [
                    '\\begin{tabular}{|c|c|c|c|}',
                    '\\hline',
                    '\\multirow{2}{*}{Queue} & \\multicolumn{3}{c|}{\#Threads Abort Rate (\%)}\\\\'
                    '\\cline{2-4}'
                    '& \quad 4 & 12 & 20\\\\',
                ]
                end_lines = [
                    '\\hline'
                    '\\end{tabular}',
                ]
                myfile = filename+str(size)+'aborts.tex'
            else:
                begin_lines = [
                    '\\begin{tabular}{|c|c|c|c|}',
                    '\\hline',
                    '\\multirow{2}{*}{Hashmap} & \\multicolumn{3}{c|}{\#Threads Abort Rate (\%)}\\\\'
                    '\\cline{2-4}'
                    '& 4 & 12 & 20\\\\',
                ]
                end_lines = [
                    '\\hline',
                    '\\end{tabular}',
                ]
                myfile = filename+testname+str(args)+'_aborts.tex'

            with open(myfile, 'w') as f:
                for line in begin_lines:
                    f.write(line+"\n")
                f.write('\\hline'+"\n")
                f.write('\\hline'+"\n")
                for i in indices:
                    datum = data[i]['aborts'][1:]
                    thread_data = []
                    for j, val in enumerate(datum):
                        if j % 2 == 1:
                            thread_data.append('{0:.3f}'.format(median(val)))
                    f.write(ds[i] + ' & ' + ' & '.join(thread_data) + '\\\\\n')
                for line in end_lines:
                    f.write(line + '\n')

    def concurrent_queues_graphs(self):
        queues = ["T-Queue1", "T-Queue2", "NT-FCQueue", "Basket", "Moir","Michael-Scott","Optimistic","Read-Write","Segmented","TsigasCycle"]
        #queues = ["T-Queue1", "T-Queue2", "NT-FCQueue", "Basket", "Max Performance of other queues","Michael-Scott","Optimistic","Read-Write","Segmented","TsigasCycle"]
        filename='concurrent/all'
        colors = ["red", "red","green"] + [(0.15*i,0.15*i, 0.15*i) for i in range(7)]
        results = self.ctests['Q:PushPop']

        patterns = ['//','','//','', '', '', '', '', '', '']
        #self.get_pushpop_graphs(queues, [1,2,4], filename, colors, patterns, results)
        self.get_pushpop_graphs(queues, range(len(queues)), filename, colors, patterns, results)

        patterns = ['--','solid','--','solid', 'solid', 'solid', 'solid', 'solid', 'solid', 'solid']
        test_names = ['Q:RandSingleOps']
        #queues = ["T-Queue1", "T-Queue2", "NT-FCQueue", "", "Max Performance of other queues","","","","",""]
        for name in test_names:
            results = self.ctests[name]
            #self.get_randops_graphs(queues, [1,2,4], filename, colors, patterns, results, name)
            self.get_randops_graphs(queues, range(len(queues)), filename, colors, patterns, results, name)

    def fcqueues_graphs(self):
        queues = ["T-Queue1", "T-Queue2", "NT-FCQueue", "NT-FCQueueWrapped", "T-FCQueue", "WT-FCQueue", "WT-Queue"]
        stoindices = [0,1]
        ntindices = [2,3]
        tindices = [1,3,4]
        lpindices = [1,6,3,4,5]
        allindices = [0,1,6,3,4,5]

        filename='fcqueues/'
        colors = ["red","red","green","green","purple","purple","red"]
        results = self.ttests['Q:PushPop']

        # CACHE MISSES
        patterns = ['//','','//','', '', '..',".."]
        self.get_cm_graphs(queues, colors, patterns, filename, queue_cache_misses)

        # PUSH POP TEST: SPEED 
        patterns = ['//','','//','', '', '..',".."]
        #self.get_pushpop_graphs(queues, stoindices, filename+"sto", colors, patterns, results)
        #self.get_pushpop_graphs(queues, ntindices, filename+"nt", colors, patterns, results)
        #self.get_pushpop_graphs(queues, tindices, filename+"t", colors, patterns, results)
        #self.get_pushpop_graphs(queues, lpindices, filename+"lp", colors, patterns, results)
        self.get_pushpop_graphs(queues, allindices, filename+"all", colors, patterns, results)

        # RAND OPS TEST
        patterns = ['--','solid','--','solid', 'solid', ':', ':']
        test_names = ['Q:RandSingleOps']
        for name in test_names:
            results = self.ttests[name]
            #self.get_randops_graphs(queues, stoindices, filename+"sto", colors, patterns, results, name)
            #self.get_randops_graphs(queues, ntindices, filename+"nt", colors, patterns, results, name)
            #self.get_randops_graphs(queues, tindices, filename+"t", colors, patterns, results, name)
            #self.get_randops_graphs(queues, lpindices, filename+"lp", colors, patterns, results, name)
            self.get_randops_graphs(queues, allindices, filename+"all", colors, patterns, results, name)

    def hashmaps_graphs(self):
        maps = ["T-Chaining", "T-CuckooIE", "T-CuckooKF", "NT-Cuckoo"]
        filename='maps/'
        colors = ["red","green","green","blue"]
        test_names = [
            "HM1M:F34,I33,E33","HM1M:F90,I5,E5",
            "HM125K:F34,I33,E33","HM125K:F90,I5,E5",
            "HM10K:F34,I33,E33","HM10K:F90,I5,E5",
        ]

        patterns = ['','//','','']
        self.get_cm_graphs(maps, colors, patterns, filename+'33', map_cache_misses_5,5)
        self.get_cm_graphs(maps, colors, patterns, filename+'33', map_cache_misses_10,10)
        self.get_cm_graphs(maps, colors, patterns, filename+'33', map_cache_misses_15,15)
        self.get_cm_graphs(maps, colors, patterns, filename+'90', map_cache_misses_5_90,5)
        self.get_cm_graphs(maps, colors, patterns, filename+'90', map_cache_misses_10_90,10)
        self.get_cm_graphs(maps, colors, patterns, filename+'90', map_cache_misses_15_90,15)
        
        patterns = ["solid","--","solid","solid"]
        for name in test_names:
            for fullness in fullnesses:
                results = self.hmtests[fullness][name]
                self.get_randops_graphs(maps, range(len(maps)), filename, colors, patterns, results, name, fullness)

def main():
    p = Plotter()
    #p.hashmaps_graphs()
    p.fcqueues_graphs()
    #p.concurrent_queues_graphs()

if __name__ == "__main__":
    main()
