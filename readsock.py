#!/usr/bin/env python
"""
Module with a Speaking process and Request handler

When ran as __main__ it launches the speaking process and listens for incoming
requests terminating with \r\n\r\n. Each request is then read aloud in the
separate process using pyttsx.

Requests are recieved over the specified socket with the given address. Exit
with Ctrl-c
"""
import asyncore
import signal
import socket
import sys

from speaker import available_voices, Speaker
from server import RequestHandler, RequestServer

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
    import argparse
    desc = r'Start readsock, reads incoming requests terminated by \r\n\r\n.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('host', type=str, help='Host IP of server')
    parser.add_argument('port', type=int, help='Port to listen on')
    parser.add_argument('--voice', help='Prefered voice')
    parser.add_argument('-ls', action='store_true', help='List all voices')

    if '-ls' in sys.argv:
        voices = available_voices()
        print('Available voices:')
        for voice in voices:
            print(voice)
    else:
        args = parser.parse_args()
        start(args.host, args.port, args.voice)
