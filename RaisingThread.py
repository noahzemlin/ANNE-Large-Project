import logging
from threading import Thread

class RaisingThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run_w_exceptions(self):
        pass
    
    def run(self):
        self.exc = None
        
        try:
            self.run_w_exceptions()
        except BaseException as e:
            self.exc = e
            logging.error("Fatal error", exc_info=True)

    def join(self):
        Thread.join(self)
        if self.exc:
            raise self.exc