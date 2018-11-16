import unittest

from pm4py.objects.random_variables.normal.random_variable import Normal
from pm4py.objects.random_variables.random_variable import RandomVariable
from pm4py.objects.random_variables.uniform.random_variable import Uniform


class RandomVariableTest(unittest.TestCase):
    def test_uniform_variable(self):
        # to avoid static method warnings in tests,
        # that by construction of the unittest package have to be expressed in such way
        self.dummy_variable = "dummy_value"
        loc = 53
        scale = 32
        tol = 0.15
        U = Uniform(loc=loc, scale=scale)
        values = [U.get_value() for i in range(100)]
        R = RandomVariable()
        R.calculate_parameters(values)
        if not R.get_distribution_type() == "UNIFORM":
            raise Exception("Expected an uniform!")
        loc_R = R.random_variable.loc
        scale_R = R.random_variable.scale
        diff_value_loc = abs(loc - loc_R) / (max(abs(loc), abs(loc_R)))
        diff_value_scale = abs(scale - scale_R) / (max(abs(scale), abs(scale_R)))
        if diff_value_loc > tol or diff_value_scale > tol:
            raise Exception("parameters found outside tolerance")

    def test_normal_variable(self):
        # to avoid static method warnings in tests,
        # that by construction of the unittest package have to be expressed in such way
        self.dummy_variable = "dummy_value"
        mu = 53
        sigma = 4
        tol = 0.15
        N = Normal(mu=mu, sigma=sigma)
        values = [N.get_value() for i in range(100)]
        R = RandomVariable()
        R.calculate_parameters(values)
        if not R.get_distribution_type() == "NORMAL":
            raise Exception("Excepted a normal!")
        mu_R = R.random_variable.mu
        sigma_R = R.random_variable.sigma
        diff_value_mu = abs(mu - mu_R) / (max(abs(mu), abs(mu_R)))
        diff_value_sigma = abs(sigma - sigma_R) / (max(abs(sigma), abs(sigma_R)))
        if diff_value_mu > tol or diff_value_sigma > tol:
            raise Exception("parameters found outside tolerance")
