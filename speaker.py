import multiprocessing
import pyttsx
import string


def available_voices():
    """
    Returns a list of available voice-ids
    """
    engine = pyttsx.init()
    voices = engine.getProperty('voices')
    return [voice.id for voice in voices]


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
        self.__printable = set(string.printable)
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
            self.__engine.say(self.__to_printable(text))
        else:
            self.__engine.endLoop()

    def __to_printable(self, text):
        return ''.join(ch for ch in text if ch in self.__printable)
