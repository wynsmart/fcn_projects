set tcpType1 [lindex $argv 0]
set tcpType2 [lindex $argv 1]
set rate [lindex $argv 2]
set log_file [lindex $argv 3]

set ns [new Simulator]
$ns color 1 Blue
$ns color 2 Red

set nf [open $log_file w]
$ns namtrace-all $nf

# Create topology
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

# create all links
$ns duplex-link $n1 $n2 10Mb 5ms DropTail
$ns duplex-link $n5 $n2 10Mb 5ms DropTail
$ns duplex-link $n2 $n3 10Mb 5ms DropTail
$ns duplex-link $n3 $n4 10Mb 5ms DropTail
$ns duplex-link $n3 $n6 10Mb 5ms DropTail

# queue limit for link n2-n3
$ns queue-limit $n2 $n3 10

# connection n1-n4 and n5-n6 TCP
set tcp1 [new $tcpType1]
set tcp2 [new $tcpType2]
$tcp1 set class_ 2
$tcp2 set class_ 2
$ns attach-agent $n1 $tcp1
$ns attach-agent $n5 $tcp2
set sink1 [new Agent/TCPSink]
set sink2 [new Agent/TCPSink]
$ns attach-agent $n4 $sink1
$ns attach-agent $n6 $sink2
$ns connect $tcp1 $sink1
$ns connect $tcp2 $sink2
$tcp1 set fid_ 1
$tcp2 set fid_ 1

# application for tcp FTP
set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1
$ftp1 set type_ FTP
set ftp2 [new Application/FTP]
$ftp2 attach-agent $tcp2
$ftp2 set type_ FTP


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
$cbr set rate_ ${rate}Mb
$cbr set random_ false

$ns at 0 "$ftp1 start"
$ns at 0 "$ftp2 start"
$ns at 0 "$cbr start"
$ns at 15 "$cbr stop"
$ns at 15 "$ftp1 stop"
$ns at 15 "$ftp2 stop"
$ns at 15 "$ns halt"

$ns run
