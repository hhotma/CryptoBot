from Strategies import Strategy

class NoSL(Strategy.Strategy):
    def definition(self, input):
        input["strategy"] = "NoSL"
        return input