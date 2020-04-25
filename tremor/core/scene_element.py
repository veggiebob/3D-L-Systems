from tremor.math.transform import Transform


class SceneElement:
    def __init__(self, name):
        self.transform = Transform()
        self.name = name

    def __str__(self):
        return self.name + " (SceneElement-" + str(self.__hash__()) + ")"
