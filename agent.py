import copy
import logging
from structs import AgentInfo
import numpy as np

class Agent:
    def __init__(self, inputs: np.ndarray, hidden_layers: np.ndarray, output: np.ndarray) -> None:
        self.network = []

        for i in range(len(hidden_layers)):
            if i == 0:
                self.network.append(np.array(
                    np.random.normal(0, 0.4, (inputs, hidden_layers[i]))
                    ))

            if i > 0 and i != len(hidden_layers) - 1:
                self.network.append(np.array(
                    np.random.normal(0, 0.4, (hidden_layers[i-1], hidden_layers[i]))
                    ))

        if len(hidden_layers) == 0:
            self.network.append(np.array(
                    np.random.normal(0, 0.4, (inputs, output))
                    ))
        else:
            self.network.append(np.array(
                    np.random.normal(0, 0.4, (inputs + hidden_layers[len(hidden_layers) - 1], output))
                    ))

    def predict(self, input: np.ndarray) -> np.ndarray:

        originput = copy.deepcopy(input)
        for i, layer in enumerate(self.network):
            if i != len(self.network) - 1:
                input = 1 / (1 + np.exp(-np.matmul(input, layer))) # Multiply each layer with sigmoid activation
            else:
                # Skip connect from first layer
                input = np.matmul(np.concatenate((input, originput)), layer)

                # Softmax
                e = np.exp(input)
                input = e / e.sum()

        return input