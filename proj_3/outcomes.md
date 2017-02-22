## E1

* which TCP variant(s) are able to get higher average throughput?
  * Vegas

* Which has the lowest average latency?
  * Vegas

* Which has the fewest drops?
  * Vegas

* Is there an overall "best" TCP variant in this experiment, or does the "best" variant vary depending on other circumstances?
  * Vegas is better under most circumstances


## E2

* Are the different combinations of variants fair to each other?
  * Reno/Reno and Vegas/Vegas are fair. NewReno/Reno amd NewReno/Vegas are combinations that are unfair to each other.

* Are there combinations that are unfair, and if so, why is the combination unfair? To explain unfairness, you will need to think critically about how the protocols are implemented and why the different choices in different TCP variants can impact fairness.
  * For NewReno/Vegas, initially NewReno uses a higher bandwidth of the channel but later as it support fast retrasnmit, Vegas starts dominating the channel bandwidth. This can be explained by the fact that Vegas does not wait for 3 duplicate ACKs before re-transmitting a lost packet. Hence higher throughput on part of Vegas. Vegas is unfair to NewReno because there are fewer retransmits due to it's slow start and congestion avoidance algorithm.
  * NewReno/Reno, NewReno have more bandwidth share as it implements Fast Retransmission instead of packet drop. Similarly, for NewReno/Vegas, it is observed that Vegas performs poorly as it detects network congestion early. Hence, though it performs well individually, it suffers with low bandwidth utilisation when paired with NewReno in the network. 


## E3

* Does each queuing discipline provide fair bandwidth to each flow?
  * No

* How does the end-to-end latency for the flows differ between DropTail and RED?
  * The latency due to DropTail and RED queueing algorithms does not differ much. Based upon our experimental observations, DropTail and RED both have same Linear trends in the latency variations.

* How does the TCP flow react to the creation of the CBR flow?
  * As CBR flow starts, TCP latency increases with occasional variations, but it remains much higher than latency without CBR.

* Is RED a good idea while dealing with SACK?
  * RED does not affect the latency of SACK, but increases the throughput slightly as comapred to DropTail. Hence RED is suitable to deal with SACK
