import numpy as np

class LoopControls:
    def __init__(self, rate, chunk, format, initial_lengths):
        self.rate = rate
        self.chunk = chunk
        self.format = format
        
        self.loop_sizes = self.calculate_loop_sizes(initial_lengths)
        self.loops = [np.zeros((size, chunk), dtype=format) for size in self.loop_sizes]
        self.loop_positions = [0] * len(self.loops)
        self.current_loop = 0
        
        self.muted_loops = [False] * len(self.loops)
        self.soloed_loops = [False] * len(self.loops)
        self.is_recording = False
        self.is_overdubbing = False

    def calculate_loop_sizes(self, loop_lengths):
        return [int(self.rate / self.chunk * length) for length in loop_lengths]

    def update_loop_length(self, loop_index, length):
        new_size = int(self.rate / self.chunk * length)
        current_loop = self.loops[loop_index]
        current_size = self.loop_sizes[loop_index]

        new_loop = np.zeros((new_size, self.chunk), dtype=self.format)

        if new_size < current_size:
            new_loop[:new_size] = current_loop[:new_size]
        else:
            num_repeats = new_size // current_size
            remainder = new_size % current_size

            for i in range(num_repeats):
                new_loop[i * current_size:(i + 1) * current_size] = current_loop

            if remainder > 0:
                new_loop[num_repeats * current_size:] = current_loop[:remainder]

        self.loops[loop_index] = new_loop
        self.loop_sizes[loop_index] = new_size
        self.loop_positions[loop_index] = 0

    def clear_loop(self, loop_index):
        self.loops[loop_index] = np.zeros_like(self.loops[loop_index])