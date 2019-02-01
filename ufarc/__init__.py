"""
Copyright 2019 Dean Hall.  See LICENSE file for details.
"""

#Desktop debugging:
#import asyncio as uasyncio
import uasyncio


class Signal(object):
    """An asynchronous stimulus that triggers reactions.
    A unique identifier that, along with a value, specifies an Event.
    p. 154
    """

    _registry = {}  # signame:str to sigid:int
    _lookup = []    # sigid:int to signame:str


    @staticmethod
    def exists(signame):
        """Returns True if signame is in the Signal registry.
        """
        return signame in Signal._registry


    @staticmethod
    def register(signame):
        """Registers the signame if it is not already registered.
        Returns the signal number for the signame.
        """
        assert type(signame) is str
        if signame in Signal._registry:
            # TODO: emit warning that signal is already registrered
            return Signal._registry[signame]
        else:
            sigid = len(Signal._lookup)
            Signal._registry[signame] = sigid
            Signal._lookup.append(signame)
            return sigid


    def __getattr__(self, signame):
        assert type(signame) is str
        return Signal._registry[signame]


# A namespace to hold pre-defined Signals
SIGNAL = Signal()


# Register the reserved (system) signals
SIGNAL.register("EMPTY") # 0
SIGNAL.register("ENTRY") # 1
SIGNAL.register("EXIT")  # 2
SIGNAL.register("INIT")  # 3
SIGNAL.register("SIGTERM") # To Exit all states


class Event(object):
    """A tuple holding ( signal, value ).
    This class holds constant values of Events
    defined by the system and used within ufarc
    and by user state machines
    """
    # Event = namedtuple("Event", ["signal", "value"])
    # Constants to index into an Event tuple
    SIG_IDX = 0
    VAL_IDX = 1

    # Instantiate the reserved (system) events
    EMPTY = (SIGNAL.EMPTY, None)
    ENTRY = (SIGNAL.ENTRY, None)
    EXIT = (SIGNAL.EXIT, None)
    INIT = (SIGNAL.INIT, None)

    # Create the SIGTERM event that helps Exit state machines
    SIGTERM = (SIGNAL.SIGTERM, None)

    # The order of this tuple MUST match their respective signals
    reserved = (EMPTY, ENTRY, EXIT, INIT)


class Hsm(object):
    """A Hierarchical State Machine (HSM).
    Full support for hierarchical state nesting.
    Guaranteed entry/exit action execution on arbitrary state transitions.
    Full support of nested initial transitions.
    Support for events with arbitrary parameters.
    """

    # Every state handler must return one of these values
    RET_HANDLED = 0
    RET_IGNORED = 1
    RET_TRAN = 2
    RET_SUPER = 3
    # TODO: the following are in qp's C code
    # but not described in book:
    # RET_UNHANDLED
    # RET_ENTRY
    # RET_EXIT
    # RET_INITIAL


    def __init__(self, initialState):
        """Sets this Hsm's current state to Hsm.top(), the default state
        and stores the given initial state.
        """
        # self.state is the Hsm's current active state.
        # This instance variable references the message handler (method)
        # that will be called whenever a message is sent to this Hsm.
        # We initialize this to self.top, the default message handler
        self.state = self.top
        self.initialState = initialState


    # Helper functions to process reserved events through the current state
    @staticmethod
    def trig(me, state, signal): return state(me, Event.reserved[signal])
    @staticmethod
    def enter(me, state): return state(me, Event.ENTRY)
    @staticmethod
    def exit(me, state): return state(me, Event.EXIT)

    # Other helper functions
    @staticmethod
    def handled(me, event): return Hsm.RET_HANDLED
    @staticmethod
    def tran(me, nextState): me.state = nextState; return Hsm.RET_TRAN
    @staticmethod
    def super(me, superState): me.state = superState; return Hsm.RET_SUPER # p. 158

    @staticmethod
    def top(me, event):
        """This is the default state handler.
        This handler ignores all signals.
        """
        sig = event[Event.SIG_IDX]

        # Handle SIGTERM to Exit the state machine
        if sig == SIGNAL.SIGTERM:
            return Hsm.RET_HANDLED

        # All events are quietly ignored
        return Hsm.RET_IGNORED # p. 165


    @staticmethod
    def init(me, event = None):
        """Transitions to the initial state.  Follows any INIT transitions
        from the inital state and performs ENTRY actions as it proceeds.
        Use this to pass any parameters to initialize the state machine.
        p. 172
        """

        # The initial state MUST transition to another state
        assert me.initialState(me, event) == Hsm.RET_TRAN

        # HSM starts in the top state
        t = Hsm.top

        # Drill into the target
        while True:

            # Store the target of the initial transition
            path = [me.state]

            # From the designated initial state, record the path to top
            Hsm.trig(me, me.state, SIGNAL.EMPTY)
            while me.state != t:
                path.append(me.state)
                Hsm.trig(me, me.state, SIGNAL.EMPTY)

            # Restore the target of the initial transition
            me.state = path[0]
            assert len(path) < 32 # MAX_NEST_DEPTH (32 is arbitrary)

            # Perform ENTRY action for each state from after-top to initial
            path.reverse()
            for s in path:
                Hsm.enter(me, s)

            # Current state becomes new source (-1 because path was reversed)
            t = path[-1]

            if Hsm.trig(me, t, SIGNAL.INIT) != Hsm.RET_TRAN:
                break

        # Current state is set to the final leaf state
        me.state = t


    @staticmethod
    def dispatch(me, event):
        """Dispatches the given event to this Hsm.
        Follows the application's state transitions
        until the event is handled or top() is reached
        p. 174
        """
        # Save the current state
        t = me.state

        # Proceed to superstates if event is not handled
        exit_path = []
        r = Hsm.RET_SUPER
        while r == Hsm.RET_SUPER:
            s = me.state
            exit_path.append(s)
            r = s(me, event)    # invoke state handler

        # If the state handler indicates a transition
        if r == Hsm.RET_TRAN:

            # Store target of transition
            t = me.state

            # Record path to top
            Hsm.trig(me, me.state, SIGNAL.EMPTY)
            while me.state != Hsm.top:
                exit_path.append(me.state)
                Hsm.trig(me, me.state, SIGNAL.EMPTY)

            # Record path from target to top
            me.state = t
            entry_path = []
            r = Hsm.RET_TRAN
            while me.state != Hsm.top:
                entry_path.append(me.state)
                Hsm.trig(me, me.state, SIGNAL.EMPTY)

            # Find the Least Common Ancestor between the source and target
            i = -1
            while exit_path[i] == entry_path[i]:
                i -= 1
            n = len(exit_path) + i + 1

            # Exit all states in the exit path
            for st in exit_path[0:n]:
                r = Hsm.exit(me, st)
                assert (r == Hsm.RET_SUPER) or (r == Hsm.RET_HANDLED)

            # Enter all states in the entry path
            # This is done in the reverse order of the path
            for st in entry_path[n::-1]:
                r = Hsm.enter(me, st)
                assert r == Hsm.RET_HANDLED, (
                        "Expected ENTRY to return "
                        "HANDLED transitioning to {0}".format(t))

            # Arrive at the target state
            me.state = t

        # Restore the current state
        me.state = t


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
        now = Framework._event_loop.time()

        # If the expiration is to happen in the past, post it now
        if expiration < now:
            tm_event.ahsm.postFIFO(tm_event)

            # If the time event is periodic, schedule its next expiration
            if tm_event.interval > 0:
                expiration = now + tm_event.interval

        # Else (the expiration is to happen in the future)
        else:

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
        Framework.run()     # TODO: rtc() here?
        Framework._event_loop.stop()


class Ahsm(Hsm):
    """An Augmented Hierarchical State Machine (AHSM); a.k.a. ActiveObject/AO.
    Adds a priority, message queue and methods to work with the queue.
    """

    def start(self, priority, initEvent=None):
        # must set the priority before Framework.add() which uses the priority
        self.priority = priority
        Framework.add(self)
        self.mq = []
        self.init(self, initEvent)
        # Run to completion
        Framework.rtc()

    def postLIFO(self, evt):
        self.mq.append(evt)

    def postFIFO(self, evt):
        self.mq.insert(0,evt)

    def pop_msg(self,):
        return self.mq.pop()

    def has_msgs(self,):
        return len(self.mq) > 0


class TimeEvent(object):
    """TimeEvent is a composite class that contains an Event.
    A TimeEvent is created by the application and added to the Framework.
    The Framework then emits the event after the given delay.
    A one-shot TimeEvent is created by calling either postAt() or postIn().
    A periodic TimeEvent is created by calling the postEvery() method.
    """
    def __init__(self, signame):
        assert type(signame) == str
        self.signal = SIGNAL.register(signame)
        self.value = None


    # Make indexing a TimeEvent work like indexing an Event tuple
    # where index 0 holds the signal and index 1 holds the value
    def __len__(self,):
        return 2
    def __getitem__(self, n):
        if n == 0:
            return self.signal
        elif n == 1:
            return self.value
        else:
            raise IndexError


    def postAt(self, ahsm, abs_time):
        """Posts this TimeEvent to the given Ahsm at a specified time.
        """
        assert issubclass(type(ahsm), Ahsm)
        self.ahsm = ahsm
        self.interval = 0
        Framework.addTimeEventAt(self, abs_time)


    def postIn(self, ahsm, delta):
        """Posts this TimeEvent to the given Ahsm after the time delta.
        """
        assert issubclass(type(ahsm), Ahsm)
        self.ahsm = ahsm
        self.interval = 0
        Framework.addTimeEvent(self, delta)


    def postEvery(self, ahsm, delta):
        """Posts this TimeEvent to the given Ahsm after the time delta
        and every time delta thereafter until disarmed.
        """
        assert issubclass(type(ahsm), Ahsm)
        self.ahsm = ahsm
        self.interval = delta
        Framework.addTimeEvent(self, delta)


    def disarm(self):
        """Removes this TimeEvent from the Framework's active time events.
        """
        self.ahsm = None
        Framework.removeTimeEvent(self)
