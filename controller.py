#-*- coding: utf-8 -*-
'''
Please add your name:Hu Yue
Please add your matric number: A0224726E
'''
import sys
import os
from sets import Set

from pox.core import core
from pox.lib.packet.ipv4 import ipv4
import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_forest

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

 
def dpid_to_mac (dpid):
    return EthAddr("%012x" % (dpid & 0xFFFFFFFFFFFF))

class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)
        # Routing table for 4 switches: Dictionary of dictionary
        self.fw_policyList = [] #firewall policy list
        self.psc = {} #Premium Service Class
        self.learnedTable = dict() # {switch -> {mac -> port}}

        
    def ip2mac(self, ip):
        return dpid_to_mac(int(ip.split('.')[-1])) 
            
    def _handle_PacketIn (self, event):   
        switch_dpid = event.connection.dpid
        inport = event.port 
        packet = event.parsed
      
         
     # install entries to the route table
        def install_enqueue(event,outport,q_id, message = None):
            message.match.dl_src = packet.src
            message.match.dl_dst = packet.dst
            message.actions.append(of.ofp_action_enqueue(port = outport, queue_id = q_id))
            message.data = event.ofp
            message.priority = 1000
            event.connection.send(message)
            log.info("switch: %s; outport: %s\n" % (switch_dpid,outport))
            log.info("installing qid: %i for %s<->%s;\n" %(q_id,packet.src,packet.dst))
    
    	# Check the packet and decide how to route the packet
        def forward(message = None):
            # check switch
            if switch_dpid not in self.learnedTable:
                self.learnedTable[switch_dpid] = dict()
            
            # check src: if pkt src[MAC:port] not recorded, store in table
            if packet.src not in self.learnedTable[switch_dpid]:
                newEntry = inport 
                self.learnedTable[switch_dpid][packet.src] = newEntry
                   
            def checkPkt(sourceip = None, destinationip = None):
                # Checks the packet type to determine where to send the packet (Task 3/4)
                if packet.type == packet.IP_TYPE:
                    log.info("Packet is IP type %s", packet.type)
                    ippacket = packet.payload
                    sourceip = ippacket.srcip
                    destinationip = ippacket.dstip
                elif packet.type == packet.ARP_TYPE:
                    log.info("Packet is ARP type %s", packet.type)
                    arppacket = packet.payload
                    sourceip = arppacket.protosrc
                    destinationip = arppacket.protodst
                else:
                    log.info("Packet is Unknown type %s", packet.type)
                    sourceip = None
                    destinationip = None
                return(sourceip,destinationip)
            
            def is_in_psc(destinationip):
                for i in self.psc[switch_dpid]:
                    if destinationip in i:
                        log.info("Destination IP %s is in list of Premium Service Class", destinationip)
                        return True
                log.info("Destination IP %s is not in list of Premium Service Class", destinationip)
                return False
            
            def make_q_id(destinationip):
                # Check if source and destination ip is in same premium service class
                qid = 0
                # If there is no address, packet is sent to a default queue 0
                # If the IP addresses are in the list of PSC, packet is sent via the Premium Queue 
                # If IP addresses are different and not in the list of PSC, packet is sent via the Normal Queue
                if destinationip == None:
                    qid = 0
                elif is_in_psc(destinationip):
                    qid = 1
                else:
                    qid = 2
                return qid
            
            (srcip,dstip) = checkPkt()
            q_id = make_q_id(dstip)
            
            # fine to add :)
            if packet.dst in self.learnedTable[switch_dpid]:
                outport = self.learnedTable[switch_dpid][packet.dst]
                install_enqueue(event,outport,q_id,message)
            # check dst: if dst is a multicast destination or pkt dst[MAC:port] not recorded
            else:
                flood(message)
         
        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
            message.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            message.data = event.ofp
            message.in_port = inport
            event.connection.send(message)
            log.info("Flood Message sent via port %i\n", of.OFPP_FLOOD)
            return

        msg = of.ofp_flow_mod() #modify flow table
        msg.hard_timeout = 5
        forward(msg)

    def _handle_ConnectionUp(self, event):
        switch_dpid = event.dpid
        log.debug("Switch %s has come up.", switch_dpid)
        self.learnedTable[switch_dpid] = {}
        self.psc[switch_dpid] = []
        
        def read_policies():
            # Firewall: reads in policy.in file
            path = "policy.in"
            reader = open(path,"r")
            nums = reader.readline().split(" ")
            numOfFW = int(nums[0])
            numOfPM = int(nums[1])
            
            for _ in range(numOfFW):
                line = reader.readline().strip().split(",")
                self.fw_policyList.append(line)
            
            for _ in range(numOfPM):
                line = reader.readline().strip().split(',')
                self.psc[switch_dpid].append(line)
            
            
        def sendFirewallPolicy(connection, policy):
            type = len(policy)    
            block = of.ofp_match()
            block.dl_type = 0x0800 # IP
            block.nw_proto = 6
            
            flow_mod = of.ofp_flow_mod()
            if (type == 2):
                block.dl_dst = EthAddr(self.ip2mac(policy[0]))
                block.tp_dst = int(policy[1]) 
                log.info("Blocking destination {} on port {}".format(policy[0],policy[1]))
            elif (type == 3):
                block.dl_src = EthAddr(self.ip2mac(policy[0]))
                block.dl_dst = EthAddr(self.ip2mac(policy[1]))
                block.tp_dst = int(policy[2])
                log.info("Blocking source {}, destination {} on port {}".format(policy[0], policy[1], policy[2]))
            flow_mod.match = block
            flow_mod.priority = 2000
            connection.send(flow_mod)  
            log.info("Firewall entry sent")
            
        read_policies()
        for i in self.fw_policyList:
            sendFirewallPolicy(event.connection, i)
        return
 
            

def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_forest.launch()

    # Starting the controller module
    core.registerNew(Controller)
