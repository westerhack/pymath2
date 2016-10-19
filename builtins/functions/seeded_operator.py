from typing import Any
from pymath2 import Undefined, Override
from pymath2.builtins.objs.math_obj import MathObj
from pymath2.builtins.variable import Variable
from pymath2.builtins.objs.named_valued_obj import NamedValuedObj
from .seeded_function import SeededFunction
class SeededOperator(SeededFunction):
	def __new__(cls, unseeded_instance: 'Operator', args: tuple, **kwargs) -> 'SeededOperator':
		for arg in args:
			if isinstance(arg, SeededOperator) and unseeded_instance is arg.unseeded_base_object:
				# print(args)
				# quit()
				pass
		return super().__new__(cls)

	@Override(SeededFunction)
	def __init__(self, **kwargs) -> None:
		super().__init__(**kwargs)
		if __debug__:
			from .operator import Operator
			assert isinstance(self.unseeded_base_object, Operator)

	@Override(SeededFunction)
	def __repr__(self) -> str:
		return '{}({!r}, {!r})'.format(self.__class__.__name__, self.unseeded_base_object, self.args)


	def _is_lower_precedence(self, other: SeededFunction) -> bool:
		if not hasattr(other, 'unseeded_base_object'):
			return False
		return self.unseeded_base_object._is_lower_precedence(other.unseeded_base_object) #should have because self.unseeded_base_object is an operator

	def _possibly_surround_in_parens(self, other: MathObj) -> str:
		if self._is_lower_precedence(other):
			return '({})'.format(other)
		return str(other)


	def _bool_oper_str(self, l, r) -> str:
		# print('Dummy Method: _bool_oper_str')
		l = self._possibly_surround_in_parens(l)
		r = self._possibly_surround_in_parens(r)
		return '{} {} {}'.format(l, self.name, r)

	@Override(SeededFunction)
	def __str__(self) -> str:
		if self.hasvalue:
			return str(self.value)
		req_arg_len = self.unseeded_base_object.req_arg_len
		if req_arg_len == 1:
			return '{}{}'.format(self.name, self._possibly_surround_in_parens(self.args[0]))
		elif req_arg_len == 2:
			return self._bool_oper_str(*(self.args if not self.unseeded_base_object.is_inverted else self.args[::-1]))
		elif req_arg_len == -1:
			from functools import reduce
			return str(reduce(lambda a, b: self._bool_oper_str(a, b), self.args))
		else:
			raise Exception('How does an operator have {} required arguments?'.
								format(self.unseeded_base_object.req_arg_len))

	@Override(SeededFunction)
	def deriv(self, du: Variable) -> ('ValuedObj', Undefined):
		return self.unseeded_base_object.deriv_w_args(du, *self.args) #await





















