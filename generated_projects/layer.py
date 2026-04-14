class Layer:
    def __init__(self):
        self.synthesis_status = False

    def synthesize(self):
        self.synthesis_status = True

    def is_synthesis_complete(self):
        return self.synthesis_status