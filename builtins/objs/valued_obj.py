from typing import Any
from pymath2 import Undefined
from .math_obj import MathObj
class ValuedObj(MathObj):
	def __init__(self, value: Any = Undefined) -> None:
		MathObj.__init__(self)
		self._value = value

	@property
	def value(self) -> (Any, Undefined):
		return self._value

	@value.setter
	def value(self, val: Any) -> None:
		self._value = val

	@value.deleter
	def fdel(self) -> None:
		self._value = Undefined

	@property
	def hasvalue(self) -> bool:
		return (self.value) is not Undefined #await

	def isconst(self, du):
		return self != du

	def deriv(self, du: 'Variable') -> ('ValuedObj', Undefined):
		return Undefined


	def d(self, other):
		from pymath2.builtins.derivative import Derivative
		return Derivative(self) / Derivative(other)

	def __abs__(self) -> float:
		return abs(float(self))

	def __bool__(self) -> bool:
		return bool(self.value)

	def __int__(self) -> int:
		return int(self.value)

	def __float__(self) -> float:
		return float(self.value)

	def __complex__(self) -> complex:
		return complex(self.value)


	def __eq__(self, other: Any) -> bool:
		if not hasattr(other, 'value'):
			return False
		return self.value == other.value

	def __str__(self) -> str:
		return self.generic_str('unvalued') if not self.hasvalue else str(self.value)

	def __repr__(self) -> str:
		return '{}({!r})'.format(type(self).__qualname__, self.value)


