#!/usr/bin/env python3


import uasyncio

import ufarc


class Three(ufarc.Ahsm):

    def initial(me, event):
        print("Three initial")
        me.te = ufarc.TimeEvent("TICK3")
        return me.tran(me, Three.running)


    def running(me, event):
        sig = event.signal
        if sig == ufarc.Signal.ENTRY:
            print("three enter")
            me.te.postEvery(me, 3)
            return me.handled(me, event)

        elif sig == ufarc.Signal.TICK3:
            print("three tick")
            return me.handled(me, event)

        elif sig == ufarc.Signal.EXIT:
            print("three exit")
            me.te.disarm()
            return me.handled(me, event)

        return me.super(me, me.top)


class Five(ufarc.Ahsm):

    def initial(me, event):
        print("Five initial")
        me.te = ufarc.TimeEvent("TICK5")
        return me.tran(me, Five.running)


    def running(me, event):
        sig = event.signal
        if sig == ufarc.Signal.ENTRY:
            print("five enter")
            me.te.postEvery(me, 5)
            return me.handled(me, event)

        elif sig == ufarc.Signal.TICK5:
            print("five tick")
            return me.handled(me, event)

        elif sig == ufarc.Signal.EXIT:
            print("five exit")
            me.te.disarm()
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    three = Three(Three.initial)
    five = Five(Five.initial)

    three.start(3)
    five.start(5)

    loop = uasyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        ufarc.Framework.stop()
    loop.close()
