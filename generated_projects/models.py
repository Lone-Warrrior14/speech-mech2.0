class SynthesisModel:
    def __init__(self):
        self.synthesis = Synthesis()

    def complete_synthesis(self):
        self.synthesis.synthesis_complete()

    def is_synthesis_complete(self):
        return self.synthesis.is_complete()