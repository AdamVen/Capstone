# Author: Adam Vengroff
# Description: This class allows for video to be both streamed and saved locally

# Video writing imports
import io


class DualOutput(object):
    def __init__(self, filename, con):
        self.output_file = io.open(filename, 'wb')
        self.output_sock = con

    def write(self, buf):
        self.output_file.write(buf)
        self.output_sock.write(buf)

    def flush(self):
        self.output_file.flush()
        self.output_sock.flush()

    def close(self):
        self.output_file.close()
        self.output_sock.close()