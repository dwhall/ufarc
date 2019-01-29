"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

from ucollections import namedtuple

from .Signal import Signal


Event = namedtuple("Event", ["signal", "value"])

# A namespace to hold pre-defined Events
class EVENT: pass

# Instantiate the reserved (system) events
EVENT.EMPTY = Event(Signal.EMPTY, None)
EVENT.ENTRY = Event(Signal.ENTRY, None)
EVENT.EXIT = Event(Signal.EXIT, None)
EVENT.INIT = Event(Signal.INIT, None)

# The order of this tuple MUST match their respective signals
EVENT.reserved = (EVENT.EMPTY, EVENT.ENTRY, EVENT.EXIT, EVENT.INIT)
