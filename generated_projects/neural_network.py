class NeuralNetwork:
    def __init__(self):
        self.layers = []

    def add_layer(self, layer):
        self.layers.append(layer)

    def synthesize(self):
        for layer in self.layers:
            layer.synthesize()

    def is_synthesis_complete(self):
        for layer in self.layers:
            if not layer.is_synthesis_complete():
                return False
        return True