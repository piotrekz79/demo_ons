#!/bin/bash

for sw in s00T s01T s32T s64T s96T s128T
do
  sudo ovs-ofctl add-flow ${sw} -O OpenFlow13 priority=101,dl_type=0x88cc,actions=CONTROLLER
done

