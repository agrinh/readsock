import asynchat
import asyncore
import collections


class RequestHandler(asynchat.async_chat):
    """
    Retrieves a request terminated by \r\n\r\n and calls callback

    Parameters
    ----------
    sock : socket
        Socket to retrieve request on
    callback : callable
        Called with entire request (str)
    """

    def __init__(self, sock, callback):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator("\r\n\r\n")
        self.__data = collections.deque(maxlen=4096)
        self.__callback = callback

    def collect_incoming_data(self, data):
        self.__data.append(data)

    def found_terminator(self):
        text = ''.join(self.__data)
        print("Received: %s" % text)
        self.__callback(text)
        self.__data.clear()


class RequestServer(asyncore.dispatcher):
    """
    Request server listening for requests on addr

    Requests are handled by RequestHandler

    Parameters
    ----------
    sock_spec : tuple
        Tuple with two items specifying (family, type) of socket. See socket
        documentation for details.
    addr : object
        Address for socket. Depends on the family and type, see socket
        documentation.

    Examples
    --------
    To open a TCP port listening for connections on port 9993 of localhost and
    printing incoming requests:

    >>> def printer(text):
    ...     print(text)
    >>> server = RequestServer((socket.AF_INET, socket.SOCK_STREAM),
                               ("localhost", 9993),
                               printer)
    >>> asyncore.loop()

    See Also
    --------
    RequestHandler : Handles incoming requests
    """

    def __init__(self, sock_spec, addr, callback):
        self.__callback = callback
        asyncore.dispatcher.__init__(self)
        self.create_socket(*sock_spec)
        self.set_reuse_addr()
        self.bind(addr)
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print("Connection from: %s" % (addr, ))
            handler = RequestHandler(sock, self.__callback)
