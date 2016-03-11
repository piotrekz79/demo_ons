#!/bin/bash

#currently on the last hop gets frame with mpls ethertype
#we should have actions=pop_mpls:0x0800 (we do not use VLANS on hosts at this moment)
sudo ovs-ofctl add-flow s128 -O OpenFlow13 "priority=9100,mpls,mpls_label=194455,mpls_bos=1,actions=pop_mpls:0x0800,set_field:00:00:10:00:03:01->eth_dst,output:4"
