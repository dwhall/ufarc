#!/usr/bin/env python3

"""UDP Relay AHSM for ufarc
This is a demonstration program that
relays UDP messages to/from the ufarc framework.

This file represents the "server" which listens for a connection.
A client such as netcat (nc) can be used to issue UDP datagrams
to the server.
When a client is present, the server starts a timer
to periodically echo back the most recently received message.
When the client is gone, the server awaits the next datagram.

References:
- https://www.pythonsheets.com/notes/python-asyncio.html
- https://docs.python.org/3.4/library/asyncio.html
"""

import uasyncio

import ufarc


UDP_PORT = 4242


class UdpServer:
    def connection_made(self, transport):
        pass

    def datagram_received(self, data, addr):
        UdpRelayAhsm.on_datagram(data, addr)

    def error_received(self, error):
        UdpRelayAhsm.on_error(error)


class UdpRelayAhsm(ufarc.Ahsm):

    def initial(me, event):
        ufarc.Framework.subscribe("NET_ERR", me)
        ufarc.Framework.subscribe("NET_RXD", me)
        me.tmr = ufarc.TimeEvent("FIVE_COUNT")

        loop = uasyncio.get_event_loop()
        server = loop.create_datagram_endpoint(UdpServer, local_addr=("localhost", UDP_PORT))
        me.transport, me.protocol = loop.run_until_complete(server)
        return me.tran(me, UdpRelayAhsm.waiting)


    def waiting(me, event):
        sig = event.signal
        if sig == ufarc.Signal.ENTRY:
            print("Awaiting a UDP datagram on port {0}.  Try: $ nc -u localhost {0}".format(UDP_PORT))
            return me.handled(me, event)

        elif sig == ufarc.Signal.NET_RXD:
            me.latest_msg, me.latest_addr = event.value
            print("RelayFrom(%s): %r" % (me.latest_addr, me.latest_msg.decode()))
            return me.tran(me, UdpRelayAhsm.relaying)

#        elif sig == ufarc.Signal.SIGTERM:
#            return me.tran(me, UdpRelayAhsm.exiting)

        return me.super(me, me.top)


    def relaying(me, event):
        sig = event.signal
        if sig == ufarc.Signal.ENTRY:
            me.tmr.postEvery(me, 5.000)
            return me.handled(me, event)

        elif sig == ufarc.Signal.NET_RXD:
            me.latest_msg, me.latest_addr = event.value
            print("RelayFrom(%s): %r" % (me.latest_addr, me.latest_msg.decode()))
            return me.handled(me, event)

        elif sig == ufarc.Signal.FIVE_COUNT:
            s = "Latest: %r\n" % me.latest_msg.decode()
            me.transport.sendto(s.encode(), me.latest_addr)
            return me.handled(me, event)

        elif sig == ufarc.Signal.NET_ERR:
            return me.tran(me, UdpRelayAhsm.waiting)

#        elif sig == ufarc.Signal.SIGTERM:
#            me.tmr.disarm()
#            return me.tran(me, UdpRelayAhsm.exiting)

        elif sig == ufarc.Signal.EXIT:
            print("Leaving timer event running so Ctrl+C will be handled on Windows")
            return me.handled(me, event)

        return me.super(me, me.top)


    def exiting(me, event):
        sig = event.signal
        if sig == ufarc.Signal.ENTRY:
            print("exiting")
            me.transport.close()
            return me.handled(me, event)
        return me.super(me, me.top)


    # Callbacks interact via messaging
    @staticmethod
    def on_datagram(data, addr):
        e = ufarc.Event(ufarc.Signal.NET_RXD, (data,addr))
        ufarc.Framework.publish(e)

    @staticmethod
    def on_error(error):
        e = ufarc.Event(ufarc.Signal.NET_ERR, (error))
        ufarc.Framework.publish(e)


if __name__ == "__main__":
    relay = UdpRelayAhsm(UdpRelayAhsm.initial)
    relay.start(0)

    loop = uasyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        ufarc.Framework.stop()
    loop.close()
