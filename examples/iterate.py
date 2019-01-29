#!/usr/bin/env python3


import uasyncio

import ufarc


class Iterate(ufarc.Ahsm):
    def __init__(self,):
        super().__init__(Iterate.initial)
        ufarc.SIGNAL.register("ITERATE")


    def initial(me, event):
        print("initial")
        me.iter_evt = ufarc.Event(ufarc.SIGNAL.ITERATE, None)
        return me.tran(me, Iterate.iterating)


    def iterating(me, event):
        sig = event.signal
        if sig == ufarc.SIGNAL.ENTRY:
            print("iterating")
            me.count = 10
            me.postFIFO(me.iter_evt)
            return me.handled(me, event)

        elif sig == ufarc.SIGNAL.ITERATE:
            print(me.count)

            if me.count == 0:
                return me.tran(me, Iterate.done)
            else:
                # do work
                me.count -= 1
                me.postFIFO(me.iter_evt)
                return me.handled(me, event)

        return me.super(me, me.top)


    def done(me, event):
        sig = event.signal
        if sig == ufarc.SIGNAL.ENTRY:
            print("done")
            ufarc.Framework.stop()
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    sl = Iterate()
    sl.start(0)

    loop = uasyncio.get_event_loop()
    loop.run_forever()
    loop.close()
