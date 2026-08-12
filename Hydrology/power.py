class PowerCalculator:
    def __init__(self):
        self.rho = 1000
        self.g = 9.81
        self.eta = 0.85

    def calculate(self, discharge, gross_head, weir_height=0):
        net_head = gross_head - weir_height
        if net_head < 0:
            net_head = 0

        power = (
            self.rho
            * self.g
            * discharge
            * net_head
            * self.eta
        ) / 1000000

        return power