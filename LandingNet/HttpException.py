class InvalidUsage(Exception):
    code = 422

    def __init__(self, msg):
        Exception.__init__(self)
        self.message = msg 
