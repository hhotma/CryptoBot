
# {'symbol': ['BAKE'], 'cp': [[0.266, 100]], 'tp': [[0.269, 45], [0.273, 50], [0.277, 100]], 'sl': [[0.127, 100]]}


class Strategy():
    def __call__(self, input):
        return self.definition(input)

    def definition(self, input):
        return input