import logging
class Debugger:
    def log(self, frame_number, entities):
        for ident,e in entities.items():
            logging.debug("Frame=%s local=%s class=%s confidence=%.3f state=%s pixel=%s position=%s",
                          frame_number, ident, e.class_name, e.confidence, e.track_state, e.ground, e.position)
class NullDebugger:
    def log(self, *args):
        pass
