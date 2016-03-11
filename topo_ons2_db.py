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
from mininet.util import waitListening
from netaddr import *
import sys
from sys import exit
import time

import MySQLdb as mdb  #global, used by returnSwitchConnections

#TODO do we really need it?

mplsVal=5100
def connectToRootNS( network, switch, ip, routes ):
    """Connect hosts to root namespace via switch. Starts network.
      network: Mininet() network object
      switch: switch to connect to root namespace
      ip: IP address for root namespace node
      routes: host networks to route to"""
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = network.addLink( root, switch ).intf1
    root.setIP( ip, intf=intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        switch = network[ 's1' ]  # switch to use
    if not routes:
        routes = [ '10.0.0.0/24' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print "*** Waiting for ssh daemons to start"
    for server in network.hosts:
        waitListening( server=server, port=22, timeout=5 )

    print
    print "*** Hosts are running sshd at the following addresses:"
    print
    for host in network.hosts:
        print host.name, host.IP()
    print
    print "*** Type 'exit' or control-D to shut down network"
    CLI( network )
    for host in network.hosts:
        host.cmd( 'kill %' + cmd )
    network.stop()




def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/24')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6653)

    info( '*** Add switches\n')
    s100 = net.addSwitch('s100', cls=OVSKernelSwitch, dpid='0064')
    s64 = net.addSwitch('s64', cls=OVSKernelSwitch, dpid='0040')
    s32 = net.addSwitch('s32', cls=OVSKernelSwitch, dpid='0020')
    s128 = net.addSwitch('s128', cls=OVSKernelSwitch, dpid='0080')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, dpid='0001')
    s96 = net.addSwitch('s96', cls=OVSKernelSwitch, dpid='0060')

    #s1 = net.addSwitch('s1', cls=UserSwitch)

    info( '*** Add hosts\n')
    h2He = net.addHost('h2He', cls=Host, ip='10.0.0.2/24', defaultRoute=None)
    h7N = net.addHost('h7N', cls=Host, ip='10.0.0.7/24', defaultRoute=None)
    h5B = net.addHost('h5B', cls=Host, ip='10.0.0.5/24', defaultRoute=None)
    h3Li = net.addHost('h3Li', cls=Host, ip='10.0.0.3/24', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(s96, s128)
    net.addLink(s128, s64)
    net.addLink(s32, s96)
    net.addLink(s32, s64)
    net.addLink(s32, s128)
    net.addLink(s128, h3Li)
    net.addLink(s96, s100)
    net.addLink(s100, s1)
    net.addLink(s1, s64)
    net.addLink(s1, h7N)
    net.addLink(s64, h2He)
    net.addLink(s32, h5B)

    #net.addLink(s1, h2He)
    #net.addLink(s1, h3Li)
    #net.addLink(s1, h5B)
    #net.addLink(s1, h7N)

    return net

def returnSwitchConnections( mn_topo, switches ):
    "Dump connections to/from nodes."

    def returnConnections( sw, swID ):
        "Helper function: dump connections to node"
        global mplsVal
        switchtable=[]
        #switchtable.append(int(sw.name.split('s')[1]))
        switchtable.append(int(swID))
        #expacted name has form openflow:<num> - this is form which
        #is retrieved form openflow
        #we cannot therefore use switchtable.append(sw.name)

        switchtable.append('openflow:' + sw.name.split('s')[1])
        switchtable.append(0)
        switchtable.append(0)
        switchtable.append(0)
        return(switchtable)


        #mn_topo.ports[sw.name].values() stores neighbours (and their ports),e.g.
        #[('s3', 2), ('s2', 2)]
        #check if there is a host on the list
        #print sw.name
        #print mn_topo.ports[sw.name].values()
        #neighs=zip(*mn_topo.ports[sw.name].values())[0] #('h2', 's1', 'h1')
        #if any('h' in s for s in neighs):
        #    mplsVal+=1
        #    switchtable.append(mplsVal)
        #else: #core switch
        #    switchtable.append(0)


    bigswitchtable=[]
    for swID, sw in enumerate(switches):
        #output( sw.name )
        bigswitchtable.append(returnConnections( sw, swID+1 ))
        #output( '\n' )
    return bigswitchtable

def returnNodeConnections( nodes, switches ):
    "Dump connections to/from nodes."

    def returnConnections( node , swIDs):
        "Helper function: dump connections to node"
        hosttable=[]
        hosttable.append(node.name)
        hosttable.append(0)
        hosttable.append(0)

        #TODO we assume host has only one link!!
        #note mn_topo.ports cannot be used as it does not return subifs
        for intf in node.intfList():

            if intf.link:
                intfs = [ intf.link.intf1, intf.link.intf2 ]
                intfs.remove( intf )
                swNamePort=intfs[0].name #has form like s2-eth3
                swNamePort=swNamePort.split('-') #['s2', 'eth3']
                hosttable.append(swIDs.index(swNamePort[0])+1)
                hosttable.append(int(swNamePort[1].split('eth')[1]))
            else:
                sys,exit('host has too many links')
        subint=intf.name.split('eth')[1].split('.') #split 0.1001 into 0 and 1001
        hosttable.append(int(subint[0]))
        hosttable.append(int(subint[1]))
        hostnet=IPNetwork(intf.IP() + '/' + intf.prefixLen)
        hosttable.append(str(hostnet.cidr))
        hosttable.append(intf.MAC())
        return(hosttable)



    bighosttable=[]
    swIDs=[sw.name for i, sw in enumerate(switches)]

    for node in nodes:
        #output( node.name )
        bighosttable.append(returnConnections( node, swIDs ))
        #output( '\n' )
    return bighosttable



def databaseDump(net):
	db = mdb.connect("localhost","coco","cocorules!","CoCoONS" )
	cursor = db.cursor()
	cursor.execute('SET FOREIGN_KEY_CHECKS=0;')

	###############
	###############
	###############   switches - create first - otherwise sites cannot be created as they reference to
	#the key present here (errno 150)

	# Drop table if it already exist using execute() method.
	cursor.execute('DROP TABLE IF EXISTS `switches`;')

	sql = """CREATE TABLE `switches` (`id` int(11) NOT NULL,  `name` varchar(45) NOT NULL,  `x` int(10) unsigned NOT NULL,  `y` int(10) unsigned NOT NULL,  `mpls_label` int(10) unsigned NOT NULL ,  PRIMARY KEY (`id`,`name`),  UNIQUE KEY `id_UNIQUE` (`id`),  UNIQUE KEY `name_UNIQUE` (`name`)  ) ENGINE=InnoDB DEFAULT CHARSET=latin1;"""
	#removed UNIQUE KEY `mpls_label_UNIQUE` (`mpls_label`) because there may be more than one core switches which have mplslabel 0
	#removed AUTOINCREMENT mpls_label - we take care of it in returnSwitchConnections

	cursor.execute(sql)
	bigswitchtable=returnSwitchConnections(net, net.switches)

	for trow in range(len(bigswitchtable)):
	    #print trow
	    #print(bighosttable[trow])
	    # Prepare SQL query to INSERT a record into the database.
	    crow=bigswitchtable[trow]
	    sql = """INSERT INTO `switches` (id, name, x, y, mpls_label) VALUES ('%d', '%s', '%d', '%d', '%d' )""" %  (crow[0],crow[1],crow[2],crow[3],crow[4])

	    try:
	    # Execute the SQL command
	        cursor.execute(sql)
	   # Commit your changes in the database
	        db.commit()
	    except:
	   # Rollback in case there is any error
	        db.rollback()



	###############   sites

	# Drop table if it already exist using execute() method.
	cursor.execute('DROP TABLE IF EXISTS sites')

	#working
	#sql = """CREATE TABLE sites (id int(10) unsigned NOT NULL AUTO_INCREMENT, name varchar(45) NOT NULL, x int(11) NOT NULL, y int(11) NOT NULL, switch int(11) NOT NULL, remote_port int(10) unsigned NOT NULL, local_port int(10) unsigned NOT NULL, vlanid int(10) unsigned NOT NULL, ipv4prefix varchar(45) NOT NULL, mac_address varchar(45) NOT NULL, PRIMARY KEY (id) )"""
	#not working
	#sql = """CREATE TABLE sites (id int(10) unsigned NOT NULL AUTO_INCREMENT, name varchar(45) NOT NULL, x int(11) NOT NULL, y int(11) NOT NULL, switch int(11) NOT NULL, remote_port int(10) unsigned NOT NULL, local_port int(10) unsigned NOT NULL, vlanid int(10) unsigned NOT NULL, ipv4prefix varchar(45) NOT NULL, mac_address varchar(45) NOT NULL, PRIMARY KEY (id), UNIQUE KEY id_UNIQUE (id), UNIQUE KEY name_UNIQUE (name),  KEY switch_idx (switch), CONSTRAINT switch_id FOREIGN KEY (switch) REFERENCES switches (id) ON DELETE NO ACTION ON UPDATE NO ACTION) ENGINE=InnoDB DEFAULT CHARSET=latin1; )"""

	sql = """CREATE TABLE `sites` (  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,  `name` varchar(45) NOT NULL,  `x` int(11) NOT NULL,  `y` int(11) NOT NULL,  `switch` int(11) NOT NULL,  `remote_port` int(10) unsigned NOT NULL,  `local_port` int(10) unsigned NOT NULL,  `vlanid` int(10) unsigned NOT NULL,  `ipv4prefix` varchar(45) NOT NULL,  `mac_address` varchar(45) NOT NULL,  PRIMARY KEY (`id`),  UNIQUE KEY `id_UNIQUE` (`id`),  UNIQUE KEY `name_UNIQUE` (`name`),  KEY `switch_idx` (`switch`),  CONSTRAINT `switch_id` FOREIGN KEY (`switch`) REFERENCES `switches` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION) ENGINE=InnoDB DEFAULT CHARSET=latin1;"""
	#
	#sql = """CREATE TABLE site( \
	#id int(10) unsigned NOT NULL AUTO_INCREMENT, \
	#name varchar(45) NOT NULL, \
	#x int(11) NOT NULL, \
	#y int(11) NOT NULL, \
	#switch int(11) NOT NULL, \
	#remote_port int(10) unsigned NOT NULL, \
	#local_port int(10) unsigned NOT NULL, \
	#vlanid int(10) unsigned NOT NULL, \
	#ipv4prefix varchar(45) NOT NULL, \
	#mac_address varchar(45) NOT NULL, \
	#PRIMARY KEY (id) )"""

	cursor.execute(sql)


	bighosttable=returnNodeConnections(net.hosts, net.switches)
	for trow in range(len(bighosttable)):
	    #print trow
	    #print(bighosttable[trow])
	    # Prepare SQL query to INSERT a record into the database.
	    crow=bighosttable[trow]
	    sql = """INSERT INTO sites (name, x, y, switch, remote_port, local_port, vlanid, ipv4prefix, mac_address)  VALUES ('%s', '%d', '%d', '%d', '%d', '%d', '%d', '%s', '%s' )""" %  (crow[0],crow[1],crow[2],crow[3],crow[4],crow[5],crow[6],crow[7],crow[8])

	    try:
	    # Execute the SQL command
	        cursor.execute(sql)
	   # Commit your changes in the database
	        db.commit()
	    except:
	   # Rollback in case there is any error
	        db.rollback()


	############### vpns

	cursor.execute('DROP TABLE IF EXISTS vpns;');

	#sql = """CREATE TABLE `vpns` (  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,  `name` varchar(45) NOT NULL,  `mpls_label` int(10) unsigned NOT NULL,  PRIMARY KEY (`id`),  UNIQUE KEY `id_UNIQUE` (`id`),  UNIQUE KEY `name_UNIQUE` (`name`),  UNIQUE KEY `mpls_label_UNIQUE` (`mpls_label`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;"""
	sql = """CREATE TABLE `vpns` (  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,  `name` varchar(45) NOT NULL,  `pathProtection` varchar(45) DEFAULT NULL,  `failoverType` varchar(45) DEFAULT NULL,  `isPublic` tinyint(1) NOT NULL,  PRIMARY KEY (`id`),  UNIQUE KEY `id_UNIQUE` (`id`),  UNIQUE KEY `name_UNIQUE` (`name`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;"""
	cursor.execute(sql)

	#sql = """INSERT INTO `vpns` VALUES (1,'all',0),(2,'vpn1',5000),(3,'vpn2',5001),(4,'vpn3',5002);"""
	#try:
	# Execute the SQL command
	#    cursor.execute(sql)
	   # Commit your changes in the database
	#    db.commit()
	#except:
	   # Rollback in case there is any error
	#    db.rollback()

	############## site2vpn
	cursor.execute('DROP TABLE IF EXISTS `site2vpn`;')
	#sql = """CREATE TABLE `site2vpn` (  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,  `vpnid` int(10) unsigned DEFAULT NULL,  `siteid` int(10) unsigned DEFAULT NULL,  PRIMARY KEY (`id`),  KEY `site_idx` (`siteid`),  KEY `vpn_idx` (`vpnid`),  CONSTRAINT `site` FOREIGN KEY (`siteid`) REFERENCES `sites` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,  CONSTRAINT `vpn` FOREIGN KEY (`vpnid`) REFERENCES `vpns` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION) ENGINE=InnoDB  DEFAULT CHARSET=latin1;"""

	sql="""CREATE TABLE `site2vpn` (	  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,	  `vpnid` int(10) unsigned DEFAULT NULL,	  `siteid` int(10) unsigned DEFAULT NULL,	  PRIMARY KEY (`id`),	  KEY `site_idx` (`siteid`),	  KEY `vpn_idx` (`vpnid`),	  CONSTRAINT `site` FOREIGN KEY (`siteid`) REFERENCES `sites` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,	  CONSTRAINT `vpn` FOREIGN KEY (`vpnid`) REFERENCES `vpns` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION	) ENGINE=InnoDB DEFAULT CHARSET=latin1;"""
	cursor.execute(sql)








	db.close()




def postconfig(net):
    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    c0 = net.controllers[0]
    net.get('s100').start([c0])
    net.get('s64').start([c0])
    net.get('s32').start([c0])
    net.get('s128').start([c0])
    net.get('s1').start([c0])
    net.get('s96').start([c0])

    #net.get('s1').start()

    info( '*** Post configure switches and hosts\n')
    net.get('h2He').cmd('vconfig add h2He-eth0 20')
    net.get('h2He').cmd('ifconfig h2He-eth0.20 up')
    net.get('h2He').cmd('ifconfig h2He-eth0.20 10.0.2.1 netmask 255.255.255.0')
    net.get('h2He').cmd('ifconfig h2He-eth0.20 hw ether 00:00:10:00:02:01')
    intf = net.get('h2He').defaultIntf()
    vlan=20
    newName = '%s.%d' % ( intf, vlan )
    intf.name = newName
    net.get('h2He').nameToIntf[ newName ] = intf
    net.get('h2He').setIP('10.0.2.1/24')
    net.get('h2He').setMAC('00:00:10:00:02:01')


    net.get('h7N').cmd('vconfig add h7N-eth0 70')
    net.get('h7N').cmd('ifconfig h7N-eth0.70 up')
    net.get('h7N').cmd('ifconfig h7N-eth0.70 10.0.7.1 netmask 255.255.255.0')
    net.get('h7N').cmd('ifconfig h7N-eth0.70 hw ether 00:00:10:00:07:01')
    intf = net.get('h7N').defaultIntf()
    vlan=70
    newName = '%s.%d' % ( intf, vlan )
    intf.name = newName
    net.get('h7N').nameToIntf[ newName ] = intf
    net.get('h7N').setIP('10.0.7.1/24')
    net.get('h7N').setMAC('00:00:10:00:07:01')


    net.get('h5B').cmd('vconfig add h5B-eth0 50')
    net.get('h5B').cmd('ifconfig h5B-eth0.50 up')
    net.get('h5B').cmd('ifconfig h5B-eth0.50 10.0.5.1 netmask 255.255.255.0')
    net.get('h5B').cmd('ifconfig h5B-eth0.50 hw ether 00:00:10:00:05:01')
    intf = net.get('h5B').defaultIntf()
    vlan=50
    newName = '%s.%d' % ( intf, vlan )
    intf.name = newName
    net.get('h5B').nameToIntf[ newName ] = intf
    net.get('h5B').setIP('10.0.5.1/24')
    net.get('h5B').setMAC('00:00:10:00:05:01')



    net.get('h3Li').cmd('vconfig add h3Li-eth0 30')
    net.get('h3Li').cmd('ifconfig h3Li-eth0.30 up')
    net.get('h3Li').cmd('ifconfig h3Li-eth0.30 10.0.3.1 netmask 255.255.255.0')
    net.get('h3Li').cmd('ifconfig h3Li-eth0.30 hw ether 00:00:10:00:03:01')
    intf = net.get('h3Li').defaultIntf()
    vlan=30
    newName = '%s.%d' % ( intf, vlan )
    intf.name = newName
    net.get('h3Li').nameToIntf[ newName ] = intf
    net.get('h3Li').setIP('10.0.3.1/24')
    net.get('h3Li').setMAC('00:00:10:00:03:01')


    #CLI(net)
    #net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    net = myNetwork()
    postconfig(net)
    time.sleep(2)
    databaseDump(net)
    CLI(net)
    net.stop()
    # get sshd args from the command line or use default args
    # useDNS=no -u0 to avoid reverse DNS lookup timeout
    #argvopts = ' '.join( sys.argv[ 1: ] ) if len( sys.argv ) > 1 else (
    #    '-D -o UseDNS=no -u0' )
    #sshd( net, opts=argvopts )
    #postconfig(net)
