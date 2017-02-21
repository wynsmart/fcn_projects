set ns [new Simulator]
set nf [open exp_one_vegas.nam w]
$ns namtrace-all $nf

proc finish {} {
        global ns nf
        $ns flush-trace
        close $nf
        exit 0
}

# Create topology
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

# create all links
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n5 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n3 $n4 10Mb 10ms DropTail
$ns duplex-link $n3 $n6 10Mb 10ms DropTail

# queue limit for link n2-n3
$ns queue-limit $n2 $n3 10

# connection n1-n4 TCP
set tcp [new Agent/TCP/Vegas]
$tcp set class_ 2
$ns attach-agent $n1 $tcp
set sink [new Agent/TCPSink]
$ns attach-agent $n4 $sink
$ns connect $tcp $sink
$tcp set fid_ 1

# application for tcp FTP
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP

# connection n2-n3 UDP
set udp [new Agent/UDP]
$ns attach-agent $n2 $udp
set udpsink [new Agent/Null]
$ns attach-agent $n3 $udpsink
$ns connect $udp $udpsink
$udp set fid_ 2

# set up CBR
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set packet_size_ 1000
$cbr set rate_ 1Mb
$cbr set random_ false

$ns at 0.1 "$ftp start"
$ns at 0.4 "$cbr start"
$ns at 0.8 "$cbr set rate_ 2Mb"
$ns at 1.0 "$cbr set rate_ 3Mb"
$ns at 1.2 "$cbr set rate_ 4Mb"
$ns at 1.4 "$cbr set rate_ 5Mb"
$ns at 1.6 "$cbr set rate_ 6Mb"
$ns at 1.8 "$cbr set rate_ 7Mb"
$ns at 2.0 "$cbr set rate_ 8Mb"
$ns at 2.2 "$cbr set rate_ 9Mb"
$ns at 2.4 "$cbr set rate_ 10Mb"
$ns at 2.6 "$cbr stop"
$ns at 2.8 "$ftp stop"
$ns at 3.0 "$ns halt"

$ns run

