# CBR Flow reversed. Now from N2 to N1

set ns [new Simulator]

$ns color 1 Blue
$ns color 2 Red

set nf [open exp_one_tahoe_4_cbr_rev.nam w]
$ns namtrace-all $nf

proc finish {} {
        global ns nf
        $ns flush-trace
        close $nf
	# exec nam exp_one_reno_2_cbr_rev.nam &
        exit 0
}

# Create topology
set n0 [$ns node]
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]

# create all links
$ns duplex-link $n0 $n1 2Mb 10ms DropTail
$ns duplex-link $n4 $n1 2Mb 10ms DropTail
$ns duplex-link $n1 $n2 2Mb 10ms DropTail
$ns duplex-link $n2 $n3 2Mb 10ms DropTail
$ns duplex-link $n2 $n5 2Mb 10ms DropTail

# queue limit for link n2-n3
$ns queue-limit $n2 $n3 10

# nam topology
$ns duplex-link-op $n0 $n1 orient right-down
$ns duplex-link-op $n4 $n1 orient right-up
$ns duplex-link-op $n1 $n2 orient right
$ns duplex-link-op $n2 $n3 orient right-up
$ns duplex-link-op $n2 $n5 orient right-down

# queue monitor for nam
$ns duplex-link-op $n1 $n2 queuePos 0.5

# connection n0-n3 TCP
set tcp [new Agent/TCP]
$tcp set class_ 2
$ns attach-agent $n0 $tcp
set sink [new Agent/TCPSink]
$ns attach-agent $n3 $sink
$ns connect $tcp $sink
$tcp set fid_ 1

# application for tcp FTP
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP

# connection n1-n2 UDP
set udp [new Agent/UDP]
$ns attach-agent $n2 $udp
set udpsink [new Agent/Null]
$ns attach-agent $n1 $udpsink
$ns connect $udp $udpsink
$udp set fid_ 2

# set up CBR
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set packet_size_ 1000
$cbr set rate_ 4mb
$cbr set random_ false

$ns at 0.1 "$cbr start"
$ns at 0.8 "$ftp start"
$ns at 4.0 "$ftp stop"
$ns at 4.2 "$cbr stop"
$ns at 4.6 "finish"

$ns run

