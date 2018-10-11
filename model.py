import os
import itertools

from variable import Variable, Expression
from collections import Iterable

class Model:
    counter = itertools.count()
    def __init__(self, name=None):
        if name is None:
            name = f'Model_{next(Model.counter)}'

        self.name = name
        self.variables = {}
        self.objective = Objective()
        self.constraints = {}

    def add_variables(self, *variables, overwrite=False):
        """
        :param variables: a pyflip.variable.Variable object, or iterable
        :param substitute: boolean for whether to allow overwriting existing model variables (by name)
        """
        for variable in variables:
            if (variable.name not in self.variables) or overwrite:
                self.variables[variable.name] = variable
            else:
                raise RuntimeError(f'A variable named {variable.name} already exists in this model')

    def add_objective(self, objective):
        """
        :param objective: a pyflip.Objective object
        """
        self.test_defined_variables(objective.expr)
        self.objective = objective

    def add_constraints(self, *constraints, overwrite=False):
        """
        :param constraint: a pyflip.Constraint object, or iterable
        :param substitute: boolean for whether to allow overwriting existing model constraints (by name)
        """
        for constraint in constraints:
            if (constraint.name not in self.constraints) or overwrite:
                self.test_defined_variables(constraint.lhs)
                self.test_defined_variables(constraint.rhs)
                self.constraints[constraint.name] = constraint
            else:
                raise RuntimeError(f'A constraint named {constraint.name} already exists in this model')

    def test_defined_variables(self, expr):
        """
        Tests that all variables using in an expression are defined in the model
        :param expr:
        """
        for var_name in expr.var_names():
            if var_name not in self.variables:
                raise RuntimeError(f'Unrecognised variable {var_name}. Variables must be added to model before a dependent constraint or objective')

    def __iadd__(self, other):
        """
        Define the 'model += object' interface
        """
        if isinstance(other, Iterable):
            first_element = next(iter(other))
            if isinstance(first_element, Variable):
                self.add_variables(*other)
            elif isinstance(first_element, Constraint):
                self.add_constraints(*other)
            else:
                return NotImplemented

        elif isinstance(other, Variable):
            self.add_variables(other)
        elif isinstance(other, Constraint):
            self.add_constraints(other)
        elif isinstance(other, Objective):
            self.add_objective(other)
        else:
            return NotImplemented

        return self

    def __repr__(self):
        lines = [f'{self.name} with {len(self.variables)} vars, {len(self.constraints)} cons']
        lines.append(str(self.objective))
        for constraint in self.constraints.values():
            lines.append(str(constraint))
        for variable in self.variables.values():
            lines.append(str(variable))
        return '\n'.join(lines)



class Objective:
    counter = itertools.count()
    def __init__(self, dir='min', expr=None, name=None):
        if name is None:
            name = f'obj_{next(Objective.counter)}'

        self.expr = Expression(expr) if expr is not None else Expression()
        self.dir = dir
        self.name = name

    def value(self, soln):
        return self.expr.value(soln)

    def __repr__(self):
        return f'{self.name}: {self.dir} {self.expr}'


class Constraint:
    counter = itertools.count()
    def __init__(self, lhs=None, mid=None, rhs=None, name=None):
        if name is None:
            name = f'con_{next(Constraint.counter)}'

        self.lhs = Expression(lhs) if lhs is not None else Expression()
        self.rhs = Expression(rhs) if rhs is not None else Expression()
        self.mid = mid if mid is not None else '<='
        self.name = name

        # rearrange constraint expressions
        self._lhs, self._rhs = Expression.rearrange_ineq(lhs, rhs)


    def __repr__(self):
        return f'{self.name}: {self.lhs} {self.mid} {self.rhs}'

# # TODO: implement these useful methods
# c.is_satisfied() -> bool
# c.viol() -> negative of slack
# c.slack() -> qty. if neg this means the constraint is violated
