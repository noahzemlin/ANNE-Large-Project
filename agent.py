import numpy as np

class Agent:
    def __init__(self, inputs, hidden, output) -> None:
        self.network = [
            np.array(np.random.normal(0, 0.4, (inputs, hidden))), # Hidden nodes
            np.array(np.random.normal(0, 0.4, (hidden, output)))  # Output
        ]

    def predict(self, input):

        for layer in self.network:
            input = 1 / (1 + np.exp(-np.matmul(input, layer))) # Multiply each layer with sigmoid activation

        return input