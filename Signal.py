__usage__ = """
    from Signal import Signal
    Signal.register("KEYPRESS")
    e = Event(Signal.KEYPRESS, 42)
"""


class Signal(object):
    """An asynchronous stimulus that triggers reactions.
    A unique identifier that, along with a value, specifies an Event.
    """

    _registry = {}
    _id = 0


    @staticmethod
    def register(signame):
        assert signame not in Signal._registry
        Signal._registry[signame] = Signal._id
        Signal._id += 1


    def __getattr__(self, name):
        return Signal._registry[name]


# Turn Signal into an instance of itself so getattr works.
# This also prevents Signal() from creating a new instance.
Signal = Signal()


# Register the reserved (system) signals
Signal.register("EMPTY") # 0
Signal.register("ENTRY") # 1
Signal.register("EXIT")  # 2
Signal.register("INIT")  # 3
