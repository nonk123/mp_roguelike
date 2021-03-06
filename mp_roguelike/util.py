import random

def color(color, text):
    return f'<span style="color: {color};">{text}</span>'

def sign(x):
    return (x > 0) - (x < 0)

def get_param(params, parameter, default=None):
    return params[parameter] if parameter in params else default

class Die:
    def __init__(self, count, sides, inc=0):
        self.count = count
        self.sides = sides
        self.inc = inc

        self.roll = self.__call__

    def __call__(self, ontop=0):
        roll = 0

        for i in range(self.count):
            roll += random.randint(1, self.sides + 1)

        return roll + self.inc + ontop
