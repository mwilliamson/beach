class Closeable(object):
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
