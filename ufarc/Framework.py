"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

import uasyncio

from .Signal import SIGNAL
from . import Event
from .Hsm import Hsm


class Framework(object):
    """Framework is a composite class that holds:
    - the uasyncio event loop
    - the registry of AHSMs
    - the set of TimeEvents
    - the handle to the next TimeEvent
    - the table subscriptions to events
    """

    _event_loop = uasyncio.get_event_loop()

    # The Framework maintains a registry of Ahsms in a list.
    _ahsm_registry = []

    # The Framework maintains a dict of priorities in use
    # to prevent duplicates.
    # An Ahsm's priority is checked against this dict
    # within the Ahsm.start() method
    # when the Ahsm is added to the Framework.
    # The dict's key is the priority (integer) and the value is the Ahsm.
    _priority_dict = {}

    # The Framework maintains a group of TimeEvents in a list.
    # The entries in the list are ( expiration time, time event ).  Only
    # the event with the next/smallest expiration time is scheduled for the
    # timeEventCallback().  As TimeEvents are added and removed, the scheduled
    # callback must be re-evaluated.  Periodic TimeEvents should only have
    # one entry in the list: the next expiration.  The timeEventCallback() will
    # add a Periodic TimeEvent back into the list with its next expiration.
    _time_events = []

    # When a TimeEvent is scheduled for the timeEventCallback(),
    # a handle is kept so that the callback may be cancelled if necessary.
    _tm_event_handle = None

    # The Subscriber Table is a dictionary.  The keys are signals.
    # The value for each key is a list of Ahsms that are subscribed to the
    # signal.  An Ahsm may subscribe to a signal at any time during runtime.
    _subscriber_table = {}


    @staticmethod
    def post(event, ahsm):
        """Posts the event to the given Ahsm's event queue.
        """
        assert isinstance(ahsm, Hsm)
        ahsm.postFIFO(event)


    @staticmethod
    def publish(event):
        """Posts the event to the message queue of every Ahsm
        that is subscribed to the event's signal.
        """
        if event[Event.SIG_IDX] in Framework._subscriber_table:
            for ahsm in Framework._subscriber_table[event[Event.SIG_IDX]]:
                ahsm.postFIFO(event)
        # Run to completion
        Framework.rtc()


    @staticmethod
    def subscribe(signame, ahsm):
        """Adds the given Ahsm to the subscriber table list
        for the given signal.  The argument, signame, is a string of the name
        of the Signal to which the Ahsm is subscribing.  Using a string allows
        the Signal to be created in the registry if it is not already.
        """
        sigid = SIGNAL.register(signame)
        if sigid not in Framework._subscriber_table:
            Framework._subscriber_table[sigid] = []
        Framework._subscriber_table[sigid].append(ahsm)


    @staticmethod
    def addTimeEvent(tm_event, delta):
        """Adds the TimeEvent to the list of time events in the Framework.
        The event will fire its signal (to the TimeEvent's target Ahsm)
        after the delay, delta.
        """
        expiration = Framework._event_loop.time() + delta
        Framework._insortTimeEvent(tm_event, expiration)


    @staticmethod
    def addTimeEventAt(tm_event, expiration):
        """Adds the TimeEvent to the list of time events in the Framework.
        The event will fire its signal (to the TimeEvent's target Ahsm)
        at the given absolute time (_event_loop.time()).
        """
        Framework._insortTimeEvent(tm_event, expiration)


    @staticmethod
    def _insortTimeEvent(tm_event, expiration):
        """Inserts a TimeEvent into the list of time events,
        sorted by the next expiration of the timer.
        If the expiration time matches an existing expiration,
        we add the smallest amount of time to the given expiration
        to avoid a key collision in the Dict
        and make the identically-timed events fire in a FIFO fashion.
        """
        # If the event is to happen in the past, post it now
        if expiration < Framework._event_loop.time():
            tm_event.ahsm.postFIFO(tm_event)
            # TODO: if periodic, need to schedule next?
            return

        # If this is the only active TimeEvent, schedule its callback
        if len(Framework._time_events) == 0:
            Framework._tm_event_handle = Framework._event_loop.call_at(
                expiration, Framework.timeEventCallback, tm_event, expiration)

        # If this event expires before the next one in the list,
        # cancel any current event and schedule this one
        elif expiration < Framework._time_events[0][0]:
            if Framework._tm_event_handle:
                Framework._tm_event_handle.cancel()
            Framework._tm_event_handle = Framework._event_loop.call_at(
                expiration, Framework.timeEventCallback, tm_event,
                expiration)

        # Put this event in the list and sort the list by expiration
        entry = (expiration, tm_event)
        Framework._time_events.append(entry)
        Framework._time_events.sort(key=lambda x: x[0])


    @staticmethod
    def removeTimeEvent(tm_event):
        """Removes the TimeEvent from the list of active time events.
        Cancels the TimeEvent's callback if there is one.
        Schedules the next event's callback if there is one.
        """
        assert len(Framework._time_events) > 0

        # If the event being removed is scheduled for callback,
        entry = Framework._time_events[0]
        if tm_event == entry[1]:

            # Remove the entry
            del Framework._time_events[0]

            # Cancel any active time event
            if Framework._tm_event_handle:
                Framework._tm_event_handle.cancel()
                Framework._tm_event_handle = None

            # Schedule the next event if there is one
            if Framework._time_events:
                next_expiration, next_event = Framework._time_events[0]
                Framework._tm_event_handle = Framework._event_loop.call_at(
                    next_expiration, Framework.timeEventCallback,
                    next_event, next_expiration)

        # Else (the event being removed is NOT scheduled for callback)
        # so just remove the event
        else:
            for entry in Framework._time_events:
                if tm_event == entry[1]:
                    Framework._time_events.remove(entry)
                    break


    @staticmethod
    def timeEventCallback(tm_event, expiration):
        """The callback function for all TimeEvents.
        Posts the event to the event's target Ahsm.
        If the TimeEvent is periodic, re-insort the event
        in the list of active time events.
        """

        # Remove this expired TimeEvent from the active list
        del Framework._time_events[0]
        Framework._tm_event_handle = None

        # Post the event to the target Ahsm
        tm_event.ahsm.postFIFO(tm_event)

        # If this is a periodic time event, schedule its next expiration
        if tm_event.interval > 0:
            Framework._insortTimeEvent(tm_event,
                expiration + tm_event.interval)

        # If not set already and there are more events, set the next event callback
        if (Framework._tm_event_handle == None and
                len(Framework._time_events) > 0):
            next_expiration, next_event = Framework._time_events[0]
            Framework._tm_event_handle = Framework._event_loop.call_at(
                next_expiration, Framework.timeEventCallback, next_event,
                next_expiration)

        # Run to completion
        Framework.rtc()


    @staticmethod
    def add(ahsm):
        """Makes the framework aware of the given Ahsm.
        """
        Framework._ahsm_registry.append(ahsm)
        assert ahsm.priority not in Framework._priority_dict, (
                "Priority MUST be unique")
        Framework._priority_dict[ahsm.priority] = ahsm


    @staticmethod
    def run():
        """Dispatches an event to the highest priority Ahsm
        until all event queues are empty (i.e. Run To Completion).
        """
        getPriority = lambda x : x.priority

        while True:
            allQueuesEmpty = True
            sorted_acts = sorted(Framework._ahsm_registry, key=getPriority)
            for ahsm in sorted_acts:
                if ahsm.has_msgs():
                    event_next = ahsm.pop_msg()
                    ahsm.dispatch(ahsm, event_next)
                    allQueuesEmpty = False
                    break
            if allQueuesEmpty:
                return


    @staticmethod
    def rtc():
        """Runs a state machine handler to completion
        in an asyncio's call_soon_threadsafe context.
        """
        Framework._event_loop.call_soon_threadsafe(Framework.run)


    @staticmethod
    def run_forever():
        """Calls uasyncio's event loop's run_forever() within a try/finally
        to ensure state machines' exit handlers are executed.
        """
        try:
            Framework._event_loop.run_forever()
        finally:
            Framework.stop()
            Framework._event_loop.close()


    @staticmethod
    def stop():
        """EXITs all Ahsms and stops the event loop.
        """
        # Disable the timer callback
        if Framework._tm_event_handle:
            Framework._tm_event_handle.cancel()
            Framework._tm_event_handle = None

        # Post SIGTERM to all Ahsms so they execute their EXIT handler
        for ahsm in Framework._ahsm_registry:
            Framework.post(Event.SIGTERM, ahsm)

        # Run to completion so each Ahsm will process SIGTERM
        Framework.run()
        Framework._event_loop.stop()
