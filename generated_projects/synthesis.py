class SynthesisCompleteException(Exception):
    pass


class Synthesis:
    def __init__(self):
        self.complete = False

    def synthesis_complete(self):
        if self.complete:
            raise SynthesisCompleteException("Synthesis is already complete")
        self.complete = True

    def is_complete(self):
        return self.complete