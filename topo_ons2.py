#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6653)

    info( '*** Add switches\n')
    s00T = net.addSwitch('s00T', cls=OVSKernelSwitch, dpid='0064')
    s64T = net.addSwitch('s64T', cls=OVSKernelSwitch, dpid='0040')
    s32T = net.addSwitch('s32T', cls=OVSKernelSwitch, dpid='0020')
    s128T = net.addSwitch('s128T', cls=OVSKernelSwitch, dpid='0080')
    s01T = net.addSwitch('s01T', cls=OVSKernelSwitch, dpid='0001')
    s96T = net.addSwitch('s96T', cls=OVSKernelSwitch, dpid='0060')

    info( '*** Add hosts\n')
    h2He = net.addHost('h2He', cls=Host, ip='10.0.0.2/24', defaultRoute=None)
    h7N = net.addHost('h7N', cls=Host, ip='10.0.0.7/24', defaultRoute=None)
    h5B = net.addHost('h5B', cls=Host, ip='10.0.0.5/24', defaultRoute=None)
    h3Li = net.addHost('h3Li', cls=Host, ip='10.0.0.3/24', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(s96T, s128T)
    net.addLink(s128T, s64T)
    net.addLink(s32T, s96T)
    net.addLink(s32T, s64T)
    net.addLink(s32T, s128T)
    net.addLink(s128T, h3Li)
    net.addLink(s96T, s00T)
    net.addLink(s00T, s01T)
    net.addLink(s01T, s64T)
    net.addLink(s01T, h7N)
    net.addLink(s64T, h2He)
    net.addLink(s32T, h5B)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s00T').start([c0])
    net.get('s64T').start([c0])
    net.get('s32T').start([c0])
    net.get('s128T').start([c0])
    net.get('s01T').start([c0])
    net.get('s96T').start([c0])

    info( '*** Post configure switches and hosts\n')
    h2He.cmd('vconfig add h2He-eth0 20')
    h2He.cmd('ifconfig h2He-eth0.20 up')
    h2He.cmd('ifconfig h2He-eth0.20 10.0.2.1 netmask 255.255.255.0')
    h2He.cmd('ifconfig h2He-eth0.20 hw ether 00:00:10:00:02:01')


    h7N.cmd('vconfig add h7N-eth0 70')
    h7N.cmd('ifconfig h7N-eth0.70 up')
    h7N.cmd('ifconfig h7N-eth0.70 10.0.7.1 netmask 255.255.255.0')
    h7N.cmd('ifconfig h7N-eth0.70 hw ether 00:00:10:00:07:01')


    h5B.cmd('vconfig add h5B-eth0 50')
    h5B.cmd('ifconfig h5B-eth0.50 up')
    h5B.cmd('ifconfig h5B-eth0.50 10.0.5.1 netmask 255.255.255.0')
    h5B.cmd('ifconfig h5B-eth0.50 hw ether 00:00:10:00:05:01')

    h3Li.cmd('vconfig add h3Li-eth0 30')
    h3Li.cmd('ifconfig h3Li-eth0.30 up')
    h3Li.cmd('ifconfig h3Li-eth0.30 10.0.3.1 netmask 255.255.255.0')
    h3Li.cmd('ifconfig h3Li-eth0.30 hw ether 00:00:10:00:03:01')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

