import copy
import logging
import random
from structs import AgentInfo
import numpy as np

class Agent:
    def __init__(self, inputs: np.ndarray, hidden_layers: np.ndarray, output: np.ndarray) -> None:
        self.network = []
        self.bias_unit = np.array([1])
        self.age = 0

        # No hidden layers special case
        if len(hidden_layers) == 0:
            self.network.append(np.array(
                    np.random.normal(0, 0.4, (inputs + 1, output))
                    ))

            self.remove_weights()
            return

        # Input layer
        for i in range(len(hidden_layers)):
            # Input layer
            if i == 0:
                self.network.append(np.array(
                    np.random.normal(0, 0.4, (inputs + 1, hidden_layers[i]))
                    ))

            # Regular layer
            if i > 0:
                self.network.append(np.array(
                    np.random.normal(0, 0.4, (hidden_layers[i-1] + 1, hidden_layers[i]))
                    ))
        
        # Output layer with skip
        self.network.append(np.array(
                np.random.normal(0, 0.4, (inputs + hidden_layers[len(hidden_layers) - 1] + 1, output))
                ))

    def remove_weights(self):
        # Zero out a bunch of weights for interesting networks
        for layer_i in range(len(self.network)):
            shape = self.network[layer_i].shape
            zero_mask = np.random.random(size=shape) > 0.5

            self.network[layer_i][zero_mask] = np.zeros(shape)[zero_mask]

    def mutate(self):
        for layer_i in range(len(self.network)):
            shape = self.network[layer_i].shape

            # Nudge non-zero weights
            adj_mask = np.random.random(size=shape) > 0.8
            non_zero_mask = self.network[layer_i] != 0

            # Randomly add/delete weights
            repl_mask = np.random.random(size=shape) > 0.9
            zero_mask = np.random.random(size=shape) > 0.9

            self.network[layer_i][adj_mask & non_zero_mask] += np.random.normal(0, 0.1, shape)[adj_mask & non_zero_mask]
            self.network[layer_i][repl_mask] = np.random.normal(0, 0.4, shape)[repl_mask]
            self.network[layer_i][zero_mask] = np.zeros(shape)[zero_mask]

    def predict(self, input: np.ndarray) -> np.ndarray:

        originput = copy.deepcopy(input)
        for i, layer in enumerate(self.network):
            # Add bias
            input = np.concatenate((input, self.bias_unit))
            
            if i != len(self.network) - 1:
                # Calculate next layer and apply sigmoid
                input = np.matmul(input, layer)
                
                # Sigmoid
                input = 1 / (1 + np.exp(-input))

                # # Relu
                # input[input < 0] = 0
            else:
                # Skip connect from first layer
                input = np.matmul(np.concatenate((input, originput)), layer)

                # Softmax
                e = np.exp(input)
                input = e / e.sum()

        return input