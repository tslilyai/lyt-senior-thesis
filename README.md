# Concurrent Algorithms in Transactional Data Structures
## Lillian Tsai

**_A thesis presented to the Harvard Department of Computer Science in partial fulfillment of the requirements for the degree of Bachelor of Arts at Harvard University._**

**May 2017**

**Advised by Professor Eddie Kohler**


## Abstract
Software transactional memory (STM) simplifies the challenging, yet increasingly critical task of parallel programming. Using STM allows programmers to reason about concurrent operations in terms of transactions—groups of operations
guaranteed to have atomic effect. Our STM system, STO (Software Transactional Objects), outperforms previous STM systems, but its performance still falls short of that of the fastest concurrent programming techniques. This work aims to make
STO as fast as these techniques, and, when this appears impossible, to characterize precisely why. We implement and benchmark the most performant concurrent programming algorithms for abstract datatypes within STO’s transactional framework. Our results indicate that certain concurrent datatype algorithms lose their scalability and performance in a transactional setting, while other algorithms successfully support transactions without incurring a crippling performance loss. We claim that this discrepancy arises because various concurrent algorithms have different levels of dependency on operation commutativity, and suffer different amounts of commutativity loss in a transactional setting. To support this claim, we pose an alternative operation interface that allows for greater operation commutativity, and, with this interface, re-implement a concurrent datatype whose performance is crippled in a transactional setting. This concurrent datatype is then able to retain its performance and scalability in a transactional setting. We conclude that examining both a datatype’s dependency on operation commutativity, and the loss of commutativity of a particular datatype interface in a transactional setting, is enough to determine whether a concurrent, non-transactional data structure will achieve high scalability and performance when integrated with STO.

## Code
<https://github.com/nathanielherman/sto/tree/cds_benchmarks>
