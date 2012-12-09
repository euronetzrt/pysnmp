#
# GETNEXT Command Generator
#
# Send a series of SNMP GETNEXT requests
#     with SNMPv3 with user 'usr-none-none', no auth and no privacy protocols
#     over IPv4/UDP
#     to an Agent at 127.0.0.1:161
#     for an OID in string form
#     stop whenever received OID goes out of initial prefix (it may be a table)
#
# This script performs similar to the following Net-SNMP command:
#
# $ snmpwalk -v3 -l authNoPriv -u usr-none-none -ObentU 127.0.0.1:161  1.3.6.1.2.1.1 
#
from pysnmp.entity import engine, config
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity.rfc3413 import cmdgen
from pysnmp.proto import rfc1902

# Initial OID prefix
initialOID = rfc1902.ObjectName('1.3.6.1.2.1.1')

# Create SNMP engine instance
snmpEngine = engine.SnmpEngine()

#
# SNMPv3/USM setup
#

# user: usr-md5-des, auth: MD5, priv DES
config.addV3User(
    snmpEngine, 'usr-none-none',
)
config.addTargetParams(snmpEngine, 'my-creds', 'usr-none-none', 'noAuthNoPriv')

#
# Setup transport endpoint and bind it with security settings yielding
# a target name (choose one entry depending of the transport needed).
#

# UDP/IPv4
config.addSocketTransport(
    snmpEngine,
    udp.domainName,
    udp.UdpSocketTransport().openClientMode()
)
config.addTargetAddr(
    snmpEngine, 'my-router',
    udp.domainName, ('127.0.0.1', 161),
    'my-creds'
)

# Error/response reciever
def cbFun(sendRequestHandle,
          errorIndication, errorStatus, errorIndex,
          varBindTable, cbCtx):
    if errorIndication:
        print(errorIndication)
        return
    if errorStatus:
        print('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
            )
        )
        return  # stop on error
    for varBindRow in varBindTable:
        for oid, val in varBindRow:
            if initialOID.isPrefixOf(oid):
                print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
            else:
                return False # signal dispatcher to stop
    return True # signal dispatcher to continue

# Prepare initial request to be sent
cmdgen.NextCommandGenerator().sendReq(
    snmpEngine,
    'my-router',
    ( (initialOID, None), ),
    cbFun
)

# Run I/O dispatcher which would send pending queries and process responses
snmpEngine.transportDispatcher.runDispatcher()