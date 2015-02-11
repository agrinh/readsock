#!/usr/bin/env python
"""
Module with a Speaking process and Request handler

When ran as __main__ it launches the speaking process and listens for incoming
requests terminating with \r\n\r\n. Each request is then read aloud in the
separate process using pyttsx.

Requests are recieved over the specified socket with the given address. Exit
with Ctrl-c
"""
import asynchat
import asyncore
import collections
import multiprocessing
import pyttsx
import signal
import socket
import sys


class Speaker(multiprocessing.Process):
    """
    Process retrieving text to speak over a Queue

    Start the process with the start method and queue things to say using the
    say method

    Parameters
    ----------
    voice_id : str, optional
        Voice ID to use for speech synthesis. Must be specified as kwarg.
    *args, **kwargs
        Arguments for the superclass multiprocessing.Process
    """

    def __init__(self, *args, **kwargs):
        self.__engine = None
        self.__say_queue = multiprocessing.Queue(100)
        self.__voice_id = kwargs.pop('voice_id', None)
        super(Speaker, self).__init__(*args, **kwargs)

    def run(self):
        """
        Inits a pyttsx engine and launches the event loop
        """
        self.__engine = engine = pyttsx.init()
        if self.__voice_id is not None:
            engine.setProperty('voice', self.__voice_id)
        engine.connect('finished-utterance', self.__next_utterance)
        engine.say('Starting voice process')
        engine.startLoop()

    def stop(self):
        """
        Stop the process
        """
        self.__say_queue.put(None)

    def say(self, text):
        """
        Queues the text to be spoken

        Parameters
        ----------
        text : str, None
            Text to be spoken. Stops the process if None.
        """
        self.__say_queue.put(text)

    def __next_utterance(self, name, completed):
        """
        Used in the event loop to wait for a new message to speak
        """
        text = self.__say_queue.get()
        if text is not None:
            self.__engine.say(text)
        else:
            self.__engine.endLoop()


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
        self.__data = collections.deque(maxlen=100)
        self.__callback = callback

    def collect_incoming_data(self, data):
        self.__data.append(data)

    def found_terminator(self):
        self.__callback(''.join(self.__data))
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
            sock, _ = pair
            handler = RequestHandler(sock, self.__callback)


def start(host, port, pref_voice):
    TCP_SOCK_SPEC = (socket.AF_INET, socket.SOCK_STREAM)
    speaker = Speaker(voice_id=pref_voice)
    server = RequestServer(TCP_SOCK_SPEC, (host, port), speaker.say)

    # Close gracefully on SIGINT
    def signal_handler(signal, frame):
        asyncore.close_all()
        speaker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start speaker, notify listening address and start loops
    speaker.start()
    speaker.say("Listening for requests on %s:%s" % (host, port))
    asyncore.loop()
    speaker.stop()


if __name__ == '__main__':
    PREF_VOICE_ID = 'com.apple.speech.synthesis.voice.karen'
    host, port = ('localhost', 9993)

    import argparse

    desc = 'Start readsock, reads incoming requests terminated by \r\n\r\n.'
    parser = argparse.ArgumentParser()
    parser.add_argument('host', type=str, help='Host IP of server')
    parser.add_argument('port', type=int, help='Port to listen on')
    parser.add_argument('--voice-id', help='ID of prefered voice')
    args = parser.parse_args()

    start(args.host, args.port, args.voice_id)
