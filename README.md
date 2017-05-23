# PYCOSE: PYthon COroutine SErver
# PYCOSE: PYthon COroutine SErver

This is a very primitive server framework which uses coroutines instead of threads etc.
This means it runs even on pythons with no async support, eg: the ESP ports of MicroPython.
On the downside that means it has to poll a lot, on the upside it means that it is very
easy to write your own event handlers: they're just regular generators which yield a lot.


