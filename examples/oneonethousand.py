#!/usr/bin/env python3


import ufarc


class Mississippi(ufarc.Ahsm):

    def initial(me, event):
        print("initial")
        me.teCount = ufarc.TimeEvent("COUNT")
        me.tePrint = ufarc.TimeEvent("PRINT")
        return me.tran(me, Mississippi.counting)


    def counting(me, event):
        sig = event[ufarc.Event.SIG_IDX]
        if sig == ufarc.SIGNAL.ENTRY:
            print("counting enter")
            me._count = 0
            me.teCount.postEvery(me, 0.001)
            me.tePrint.postEvery(me, 1.000)
            return me.handled(me, event)

        elif sig == ufarc.SIGNAL.COUNT:
            me._count += 1
            return me.handled(me, event)

        elif sig == ufarc.SIGNAL.PRINT:
            print(me._count, "millis")
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    print("Check to see how much CPU% a simple 1ms periodic function uses.")
    ms = Mississippi(Mississippi.initial)
    ms.start(0)

    ufarc.Framework.run_forever()
