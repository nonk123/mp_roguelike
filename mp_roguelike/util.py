import random

def color(color, text):
    return f'<span style="color: {color};">{text}</span>'

class Die:
    def __init__(self, count, sides, inc=0):
        self.count = count
        self.sides = sides
        self.inc = inc

        self.roll = self.__call__

    def __call__(self, ontop=0):
        roll = 0

        for i in range(self.count):
            roll += random.randint(1, self.sides)

        return roll + self.inc + ontop
