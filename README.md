# ufarc

ufarc is a fork and rewrite of farc for [MicroPython](http://micropython.org).

Known Issue: Nothing works yet.

## farc

Framework for Asyncio/Actor/AHSM Run-to-completion Concurrency written in Python3.
In other words, a cheap knock-off of QP (www.state-machine.com)
that uses coroutines instead of threads.
[This book](https://newcontinuum.dl.sourceforge.net/project/qpc/doc/PSiCC2.pdf)
describes QP and how to program hierarchical state machines.

This framework has fewer than 1000 LOC.  It allows the programmer to create highly-concurrent
programs by using a message-passing system and run-to-completion message handlers
within a state-machine architecture.  With these tools, complex, asynchronous operations
are decomposed into manageable chunks of code.


## Code Repository

https://github.com/dwhall/ufarc


## Release History

2019/01/28  Initialized repo by forking farc at b9db67b56099b463cc079bdcf83d3530f305cd1b
