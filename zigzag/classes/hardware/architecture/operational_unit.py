from typing import List

## General class for a unit that performs a certain operation. For example: a multiplier unit.
class OperationalUnit:
    
    ## The class constructor
    # @param input_precision: The bit precision of the operation inputs.
    # @param output_precision: The bit precision of the operation outputs.
    # @param unit_cost: The energy cost of performing a single operation.
    # @param unit_area: The area of a single operational unit.
    def __init__(
        self,
        input_precision: List[int],
        output_precision: int,
        unit_cost: float,
        unit_area: float,
    ):
        self.input_precision = input_precision
        self.output_precision = output_precision
        self.precision = input_precision + [output_precision]
        self.cost = unit_cost
        self.area = unit_area

    ## JSON Representation of this class to save it to a json file.
    def __jsonrepr__(self):
        return self.__dict__

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, OperationalUnit):
            return False
        return (
            self.precision == __o.precision
            and self.cost == __o.cost
            and self.area == __o.area
        )


## Description missing
class Multiplier(OperationalUnit):

    ## The class constructor
    # @param input_precision: The bit precision of the multiplication inputs.
    # @param energy_cost: The energy cost of performing a single multiplication.
    # @param area: The area of a single multiplier.
    def __init__(self, input_precision: List[int], energy_cost: float, area: float):
        output_precision = sum(input_precision)
        super().__init__(input_precision, output_precision, energy_cost, area)


class FunctionalUnit(OperationalUnit):

    ## The class constructor
    # @param input_precision: The bit precision of the Functional unit's inputs.
    # @param energy_cost: The energy cost of performing a single operation on the functional unit.
    # @param area: The area of a single functional unit.
    def __init__(self, input_precision: List[int], energy_cost: float, area: float, type: str):
        output_precision = self.get_output_precision(input_precision, type)
        super().__init__(input_precision, output_precision, energy_cost, area)
    
    def get_output_precision(self, input_precision, type):
        if type == "multiplier":
            output_precision = sum(input_precision)
        else:
            raise ValueError("Given functional unit type is non existent or currently not supported. Try using multiplier.")
        return output_precision