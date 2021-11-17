'''
Please add your name: Hu Yue
Please add your matric number: A0224726E
'''

import os
import sys
import atexit
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.link import Link
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections

net = None
SERVER_IP = '127.0.0.1'

class TreeTopo(Topo):

    def __init__(self):
        # Initialize topology
        Topo.__init__(self)
        file = open('topology.in')
        [hostNum, switchNum, linkNum] = [int(x) for x in file.readline().split(' ')]
         

        # add hosts
        hosts = []
        for i in range(hostNum):
            host = self.addHost('h%d' % (i+1))
            hosts.append(host)
        info(hosts)
            

        # add switches
        switches = []
        for i in range(switchNum):
            sconfig = {'dpid': "%016x" % (i+1)}
            switch = self.addSwitch('s%d' % (i+1), **sconfig)
            switches.append(switch)
        
        info(switches)
        info(self.switches())
        
        # add links
        self.linkInfos = []
        for i in range(linkNum):
            link = file.readline().strip().split(',')
            self.linkInfos.append(link)
            firstnode = link[0]
            secondnode = link[1]
            # Links are added without bandwidth as bandwidth is added in the queue
            self.addLink(firstnode, secondnode)
            info(link)
        info(self.links(True, False, True))
        file.close()




def startNetwork():
    info('** Creating network and run simple performance test\n')
    topo = TreeTopo()
    global net
    # modify the ip address if you are using a remote pox controller
    net = Mininet(topo=topo, link=Link,
                  controller=lambda name: RemoteController(
                      name, ip= SERVER_IP),
                  listenPort=6633, autoSetMacs=True)
    info('** Starting the network\n')
    
    net.start()
        # Used to calculate the link speed between nodes in bits per second (Task 1)
    def getLinkSpeed(firstnode, secondnode):
        for i in topo.linkInfos:
            if firstnode == i[0] and secondnode == i[1]:
                return int(i[2]) * 1000000

        return 0
    
    info('Creating QoS\n')
    cnt = 0
    for link in topo.links(True, False, True):
        for s in topo.switches():
            # If one end of the link is a switch, we need to do QoS
            for i in [1,2]:
                [d1,d2,linkInfo] = link
                if (linkInfo['node%i' % i] == s):
                    port = linkInfo['port%i' % i]
                    bw = getLinkSpeed(linkInfo["node1"], linkInfo["node2"])
                    # premium_low = premium tier lower bound guarantee
                    # normal_high = regular tier upper bound
                    premium_low,normal_high =  0.8*bw, 0.5*bw

                    #  Create QoS Queues
                    # Interface name is <switch>-eth<port>
                    # q0 = normal tier
                    # q1 = premium tier
                    interface = '%s-eth%s' % (s, port)
                    cnt += 1
                    info("link: %s<->%s;sw: %s; inf: %s; \n" %(d1,d2,s,interface))
                    info("bw: %i, q0_high: %i; q1_low:%i\n" %(bw,normal_high,premium_low))
                    os.system("sudo ovs-vsctl -- set Port %s qos=@newqos \
                            -- --id=@newqos create QoS type=linux-htb other-config:max-rate=%i queues=0=@q0,1=@q1,2=@q2 \
                            -- --id=@q0 create queue other-config:max-rate=%i other-config:min-rate=%i \
                            -- --id=@q1 create queue other-config:min-rate=%i \
                            -- --id=@q2 create queue other-config:max-rate=%i" % (interface, bw, bw, bw, premium_low, normal_high))

    
    info("running CLI")
    CLI(net)

    
def stopNetwork():
    if net is not None:
        net.stop()
    # Remove QoS and Queues
    os.system('sudo ovs-vsctl --all destroy Qos')
    os.system('sudo ovs-vsctl --all destroy Queue')

if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
