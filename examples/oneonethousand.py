#!/usr/bin/env python3


import asyncio

import farc


class Mississippi(farc.Ahsm):

    def initial(me, event):
        print("initial")
        me.teCount = farc.TimeEvent("COUNT")
        me.tePrint = farc.TimeEvent("PRINT")
        return me.tran(me, Mississippi.counting)


    def counting(me, event):
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            print("counting enter")
            me._count = 0
            me.teCount.postEvery(me, 0.001)
            me.tePrint.postEvery(me, 1.000)
            return me.handled(me, event)

        elif sig == farc.Signal.COUNT:
            me._count += 1
            return me.handled(me, event)

        elif sig == farc.Signal.PRINT:
            print(me._count, "millis")
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    print("Check to see how much CPU% a simple 1ms periodic function uses.")
    ms = Mississippi(Mississippi.initial)
    ms.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()
