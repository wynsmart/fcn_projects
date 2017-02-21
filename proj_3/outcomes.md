## E1

* which TCP variant(s) are able to get higher average throughput?
  * Vegas

* Which has the lowest average latency?
  * Vegas

* Which has the fewest drops?
  * Vegas

* Is there an overall "best" TCP variant in this experiment, or does the "best" variant vary depending on other circumstances?
  * Vegas is better under some circumstances


## E2

* Are the different combinations of variants fair to each other?
  * Reno/Reno and Vegas/Vegas are fair. NewReno/Reno, NewReno have more bandwidth share as it implements Fast Retransmission instead of packet drop. Similarly, for NewReno/Vegas, it is observed that Vegas performs poorly as it detects network congestion early. Hence, though it performs well individually, it suffers with low bandwidth utilisation when paired with NewReno in the network.

* Are there combinations that are unfair, and if so, why is the combination unfair? To explain unfairness, you will need to think critically about how the protocols are implemented and why the different choices in different TCP variants can impact fairness.
  * ss


## E3

* Does each queuing discipline provide fair bandwidth to each flow?
  * No

* How does the end-to-end latency for the flows differ between DropTail and RED?
  * aa

* How does the TCP flow react to the creation of the CBR flow?
  * aa

* Is RED a good idea while dealing with SACK?
  * aa