"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

from .Signal import SIGNAL


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
