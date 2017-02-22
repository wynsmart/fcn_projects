set ns [new Simulator]

set nf [open exp_2_all_tcp.nam w]
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

# connection n1-n4 and n5- n6 TCP
set tcp1 [new Agent/TCP/Newreno]
set tcp2 [new Agent/TCP/Vegas]
set tcp3 [new Agent/TCP]
set tcp4 [new Agent/TCP/Reno]

$tcp1 set class_ 2
$tcp2 set class_ 2
$tcp3 set class_ 2
$tcp4 set class_ 2

$ns attach-agent $n1 $tcp1
$ns attach-agent $n1 $tcp2
$ns attach-agent $n1 $tcp3
$ns attach-agent $n1 $tcp4

set sink1 [new Agent/TCPSink]
set sink2 [new Agent/TCPSink]
set sink3 [new Agent/TCPSink]
set sink4 [new Agent/TCPSink]

$ns attach-agent $n4 $sink1
$ns attach-agent $n4 $sink2
$ns attach-agent $n4 $sink3
$ns attach-agent $n4 $sink4

$ns connect $tcp1 $sink1
$ns connect $tcp2 $sink2
$ns connect $tcp3 $sink3
$ns connect $tcp4 $sink4

$tcp1 set fid_ 1
$tcp2 set fid_ 1
$tcp3 set fid_ 1
$tcp4 set fid_ 1

# application for tcp FTP
set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1
$ftp1 set type_ FTP

set ftp2 [new Application/FTP]
$ftp2 attach-agent $tcp2
$ftp2 set type_ FTP

set ftp3 [new Application/FTP]
$ftp3 attach-agent $tcp3
$ftp3 set type_ FTP

set ftp4 [new Application/FTP]
$ftp4 attach-agent $tcp4
$ftp4 set type_ FTP

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

$ns at 0.1 "$ftp1 start"
$ns at 0.1 "$ftp2 start"
$ns at 0.1 "$ftp3 start"
$ns at 0.1 "$ftp4 start"
$ns at 0.6 "$cbr start"
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
$ns at 2.8 "$ftp1 stop"
$ns at 2.8 "$ftp2 stop"
$ns at 2.8 "$ftp3 stop"
$ns at 2.8 "$ftp4 stop"
$ns at 2.8 "finish"

$ns run
