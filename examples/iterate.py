#!/usr/bin/env python3


import uasyncio

import farc


class Iterate(farc.Ahsm):
    def __init__(self,):
        super().__init__(Iterate.initial)
        farc.Signal.register("ITERATE")


    def initial(me, event):
        print("initial")
        me.iter_evt = farc.Event(farc.Signal.ITERATE, None)
        return me.tran(me, Iterate.iterating)


    def iterating(me, event):
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            print("iterating")
            me.count = 10
            me.postFIFO(me.iter_evt)
            return me.handled(me, event)

        elif sig == farc.Signal.ITERATE:
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
        if sig == farc.Signal.ENTRY:
            print("done")
            farc.Framework.stop()
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    sl = Iterate()
    sl.start(0)

    loop = uasyncio.get_event_loop()
    loop.run_forever()
    loop.close()
