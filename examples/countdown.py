#!/usr/bin/env python3


import uasyncio

import ufarc


class Countdown(ufarc.Ahsm):
    def __init__(self, count=3):
        super().__init__(Countdown.initial)
        self.count = count


    def initial(me, event):
        print("initial")
        me.te = ufarc.TimeEvent("TIME_TICK")
        return me.tran(me, Countdown.counting)


    def counting(me, event):
        sig = event[ufarc.Event.SIG_IDX]
        if sig == ufarc.SIGNAL.ENTRY:
            print("counting")
            me.te.postIn(me, 1.0)
            return me.handled(me, event)

        elif sig == ufarc.SIGNAL.TIME_TICK:
            print(me.count)

            if me.count == 0:
                return me.tran(me, Countdown.done)
            else:
                me.count -= 1
                me.te.postIn(me, 1.0)
                return me.handled(me, event)

        return me.super(me, me.top)


    def done(me, event):
        sig = event[ufarc.Event.SIG_IDX]
        if sig == ufarc.SIGNAL.ENTRY:
            print("done")
            ufarc.Framework.stop()
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    sl = Countdown(10)
    sl.start(0)

    loop = uasyncio.get_event_loop()
    loop.run_forever()
    loop.close()
