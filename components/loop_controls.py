import numpy as np

class LoopControls:
    def __init__(self, rate, chunk, format, initial_lengths):
        self.rate = rate
        self.chunk = chunk
        self.format = format
        
        self.loops = {}
        self.loop_sizes = {}
        self.loop_positions = {}
        self.muted_loops = {}
        self.soloed_loops = {}
        self.next_id = 0

        for length in initial_lengths:
            self._add_loop(length)
        
        self.current_loop_id = next(iter(self.loops)) if self.loops else None
        self.is_recording = False
        self.is_overdubbing = False

    def calculate_loop_sizes(self, loop_lengths):
        return [int(self.rate / self.chunk * length) for length in loop_lengths]

    def update_loop_length(self, loop_id, length):
        if loop_id not in self.loops:
            return
            
        new_size = int(self.rate / self.chunk * length)
        current_loop = self.loops[loop_id]
        current_size = self.loop_sizes[loop_id]

        new_loop = np.zeros((new_size, self.chunk), dtype=self.format)

        if new_size < current_size:
            new_loop[:new_size] = current_loop[:new_size]
        else:
            num_repeats = new_size // current_size
            remainder = new_size % current_size

            for i in range(num_repeats):
                new_loop[i*current_size:(i+1)*current_size] = current_loop

            if remainder > 0:
                new_loop[num_repeats*current_size:] = current_loop[:remainder]

        self.loops[loop_id] = new_loop
        self.loop_sizes[loop_id] = new_size
        self.loop_positions[loop_id] = 0

    def clear_loop(self, loop_id):
        if loop_id in self.loops:
            self.loops[loop_id].fill(0)

    def _add_loop(self, length):
        loop_id = self.next_id
        size = int(self.rate / self.chunk * length)
        
        self.loops[loop_id] = np.zeros((size, self.chunk), dtype=self.format)
        self.loop_sizes[loop_id] = size
        self.loop_positions[loop_id] = 0
        self.muted_loops[loop_id] = False
        self.soloed_loops[loop_id] = False
        
        self.next_id += 1
        return loop_id

    def delete_loop(self, loop_id):
        if len(self.loops) <= 1:
            raise ValueError("Must keep at least one loop")
            
        # Clean up all references
        del self.loops[loop_id]
        del self.loop_sizes[loop_id]
        del self.loop_positions[loop_id]
        del self.muted_loops[loop_id]
        del self.soloed_loops[loop_id]
        
        # Update current selection if needed
        if self.current_loop_id == loop_id:
            self.current_loop_id = next(iter(self.loops)) if self.loops else None