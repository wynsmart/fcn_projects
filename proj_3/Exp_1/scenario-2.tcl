set tcpType [lindex $argv 0]
set rate [lindex $argv 1]
set trace_file [lindex $argv 2]

set ns [new Simulator]
set nf [open $trace_file w]
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

# connection n1-n4 TCP
set tcp [new $tcpType]
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

# connection n3-n2 UDP
set udp [new Agent/UDP]
$ns attach-agent $n3 $udp
set udpsink [new Agent/Null]
$ns attach-agent $n2 $udpsink
$ns connect $udp $udpsink
$udp set fid_ 2

# set up CBR
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set packet_size_ 1000
$cbr set rate_ ${rate}Mb
$cbr set random_ false

$ns at 0 "$ftp start"
$ns at 0 "$cbr start"
$ns at 15 "$cbr stop"
$ns at 15 "$ftp stop"
$ns at 15 "$ns halt"

$defaultRNG seed 0
$ns run
