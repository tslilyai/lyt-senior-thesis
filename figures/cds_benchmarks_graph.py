#!/usr/bin/python3

#set up matplotlib and the figure
import matplotlib.pyplot as plt
import matplotlib.colors as pcolors
from collections import defaultdict

class Plotter():
    TESTS = ["PQRandSingleOps:R","PQRandSingleOps:D","PQPushPop:R",
                "PQPushPop:D", "PQPushOnly:R", "PQPushOnly:D", 
                "Q:PushPop","Q:RandSingleOps", "Q:RandMultiOps",
                "HM1M:F34,I33,E33","HM1M:F90,I5,E5",
                "HM1MMultiOp:F34,I33,E33","HM1MMultiOp:F90,I5,E5",
                "HM125K:F34,I33,E33","HM125K:F90,I5,E5",
                "HM10K:F34,I33,E33","HM10K:F90,I5,E5",
            ]
    CONCURRENT_BENCHMARK_FILE = "concurrent/concurrent_queues.data"
    TXNAL_BENCHMARK_FILE = "txnal/txnal_queues.data"
    INIT_SIZES = [10000, 50000, 100000]
    NTHREADS = [1,2,4,8,12,16,20]

    def __init__(self):
        self._parse_stats_file()

    def _parse_stats_file(self):
        '''
        The data file cds_benchmarks_stats.txt should be parsed into 
        a dictionary with the following format:
            
            test_name {
                size1: [
                    [data structure data for 1 threads],
                    [data structure data for 2 threads],
                    ...
                ]
                size2: [
                    [data structure data for 1 threads],
                    [data structure data for 2 threads],
                    ...
                ]
            }
        ''' 
        ctests = defaultdict(dict)
        size_index = 0
        test = ""
        with open(Plotter.CONCURRENT_BENCHMARK_FILE, "r") as f:
            for line in f.read().splitlines():
                if (line == ""):
                    size_index += 1
                    size_index %= len(Plotter.INIT_SIZES)
                elif line in Plotter.TESTS:
                    test = line    
                    size_index = 0
                else:
                    if Plotter.INIT_SIZES[size_index] not in ctests[test]:
                        ctests[test][Plotter.INIT_SIZES[size_index]] = []
                    ctests[test][Plotter.INIT_SIZES[size_index]].append(
                            [float(x) for x in line.split(",")[:-1]])
        self.ctests = ctests
        ttests = defaultdict(dict)
        with open(Plotter.TXNAL_BENCHMARK_FILE, "r") as f:
            for line in f.read().splitlines():
                if (line == ""):
                    size_index += 1
                    size_index %= len(Plotter.INIT_SIZES)
                elif line in Plotter.TESTS:
                    test = line    
                    size_index = 0
                else:
                    if Plotter.INIT_SIZES[size_index] not in ttests[test]:
                        ttests[test][Plotter.INIT_SIZES[size_index]] = []
                    ttests[test][Plotter.INIT_SIZES[size_index]].append(
                            [float(x) for x in line.split(",")[:-1]])
        self.ttests = ttests

    def concurrent_queues_graphs(self):
        queues = ["STO1", "STO2", "Basket", "Moir","Michael-Scott","Optimistic","Read-Write","Segmented","TsigasCycle","Flat Combining"]
        filename='concurrent/'
        tests = self.ctests

        colors = ["red","red","grey","grey","grey","grey","grey","grey","grey","green"]

        results = tests['Q:PushPop']
        
        width = 0.07
        x = range(len(Plotter.INIT_SIZES)) 
       
        # PUSH POP TEST
        fig = plt.figure(figsize=(15,20))
        ax = fig.add_subplot(111)
        qbars = []
        qdata = defaultdict(list)
        for i, (size, data_lists) in enumerate(results.items()):
            if len(data_lists[0]) == 0:
                continue
            for q_index in range(len(data_lists[0])):
                for i in range(len(data_lists)):
                    qdata[q_index].append(data_lists[i][q_index])
        for i, (q, qdata) in enumerate(qdata.items()):
            qbars.append(ax.bar(x, qdata, width, color=colors[i]))
            x = [v+width for v in x]

        ax.set_xlim(-width,width*len(x)*len(queues)+20*width)
        legend = ax.legend(qbars, queues, loc='best', ncol=1, prop={'size':12})
        ax.set_xlabel('Initial Size')
        ax.set_ylabel('Speed (ops/s)')
        ax.set_title('Queue 2-Thread Push/Pop Test')
        xTickMarks = Plotter.INIT_SIZES 
        ax.set_xticks([v-width*(len(queues)/2) for v in x])
        xtickNames = ax.set_xticklabels(xTickMarks)
        plt.setp(xtickNames, fontsize=10)
        
        plt.savefig(filename+"%s.png" % 'Q:PushPop')
        #plt.show()
        plt.close()

        # RAND OPS TEST
        test_names = ['Q:RandSingleOps', 'Q:RandMultiOps']
        for name in test_names:
            results = tests[name]
            for i, (size, data_lists) in enumerate(results.items()):
                qdata = defaultdict(list)
                if len(data_lists[0]) == 0:
                    continue
                #plot data
                fig = plt.figure(figsize=(10,15))
                for q_index in range(len(data_lists[0])):
                    for i in range(len(data_lists)):
                        qdata[q_index].append(data_lists[i][q_index])
                for i in range(len(data_lists[0])):
                    plt.plot(Plotter.NTHREADS, qdata[i], label=queues[i], color=colors[i])

                #add in labels and title
                plt.ylabel("Speed (ops/s)")
                plt.title("%s (Initial Size %d)" % (name, size))

                #add limits to the x and y axis
                plt.xlim(1, 20)
                plt.ylim(0, 40000000)
                plt.legend(loc='upper right', ncol=2, prop={'size':12})

                #save figure to png
                plt.xlabel("Number of Threads")
                plt.savefig(filename+"%s%d.png" % (name, size))
                #plt.show()
                plt.close()

    def fcqueues_graphs(self):
        queues = ["STO1", "STO2", "FCQueue NT", "Wrapped-FCQueueNT", "STO-FCQueue"]
        filename='txnal/'
        tests = self.ttests

        colors = ["red","red","grey","grey","green"]

        results = tests['Q:PushPop']
        
        width = 0.07
        x = range(len(Plotter.INIT_SIZES)) 
       
        fig = plt.figure(figsize=(15,20))
        ax = fig.add_subplot(111)
        qbars = []
        qdata = defaultdict(list)
        for i, (size, data_lists) in enumerate(results.items()):
            if len(data_lists[0]) == 0:
                continue
            for q_index in range(len(data_lists[0])):
                for i in range(len(data_lists)):
                    qdata[q_index].append(data_lists[i][q_index])
        for i, (q, qdata) in enumerate(qdata.items()):
            qbars.append(ax.bar(x, qdata, width, color=colors[i]))
            x = [v+width for v in x]

        ax.set_xlim(-width,width*len(x)*len(queues)+20*width)
        legend = ax.legend(qbars, queues, loc='best', ncol=1, prop={'size':12})
        ax.set_xlabel('Initial Size')
        ax.set_ylabel('Speed (ops/s)')
        ax.set_title('Queue 2-Thread Push/Pop Test')
        xTickMarks = Plotter.INIT_SIZES 
        ax.set_xticks([v-width*(len(queues)/2) for v in x])
        xtickNames = ax.set_xticklabels(xTickMarks)
        plt.setp(xtickNames, fontsize=10)
        
        plt.savefig(filename+"%s.png" % 'Q:PushPop')
        #plt.show()
        plt.close()

        tests = self.ttests

        # RAND OPS TEST
        test_names = ['Q:RandSingleOps', 'Q:RandMultiOps']
        for name in test_names:
            results = tests[name]
            for i, (size, data_lists) in enumerate(results.items()):
                qdata = defaultdict(list)
                if len(data_lists[0]) == 0:
                    continue
                #plot data
                fig = plt.figure(figsize=(10,15))
                for q_index in range(len(data_lists[0])):
                    for i in range(len(data_lists)):
                        qdata[q_index].append(data_lists[i][q_index])
                for i in range(len(data_lists[0])):
                    plt.plot(Plotter.NTHREADS, qdata[i], label=queues[i], color=colors[i])

                #add in labels and title
                plt.ylabel("Speed (ops/s)")
                plt.title("%s (Initial Size %d)" % (name, size))

                #add limits to the x and y axis
                plt.xlim(1, 20)
                plt.ylim(0, 40000000)
                plt.legend(loc='upper right', ncol=2, prop={'size':12})

                #save figure to png
                plt.xlabel("Number of Threads")
                plt.savefig(filename+"%s%d.png" % (name, size))
                #plt.show()
                plt.close()

def main():
    p = Plotter()
    p.concurrent_queues_graphs()
    p.fcqueues_graphs()

if __name__ == "__main__":
    main()
