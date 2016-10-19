from typing import Any
from pymath2 import Undefined
from .named_obj import NamedObj
from .valued_obj import ValuedObj
class NamedValuedObj(NamedObj, ValuedObj):
	def __init__(self, name: str = Undefined, value: Any = Undefined) -> None:
		super().__init__(name = name)
		super().__init__(value = value)
		quit()
	def __str__(self) -> str:
		return ValuedObj.__str__(self) if self.hasvalue else NamedObj.__str__(self)

	def __repr__(self) -> str:
		return '{}({!r}, {!r})'.format(type(self).__qualname__,
					self.name,
					self.value)

	def __eq__(self, other):
		if self.name is Undefined:
			return self is other
		if NamedObj.__eq__(self, other) and self.name is not Undefined:
			return True
		return ValuedObj.__eq__(self, other) and self.value is not Undefined


