from typing import Callable
from functools import reduce

from pymath2 import Undefined, future, await_result
from pymath2.builtins.variable import Variable
from pymath2.builtins.objs.valued_obj import ValuedObj
from pymath2.builtins.objs.named_obj import NamedObj

from .unseeded_function import UnseededFunction
from .seeded_operator import SeededOperator

class Operator(UnseededFunction, NamedObj):
	seeded_type = SeededOperator
	is_inverted = False
	def __init__(self, name: str,
				 priority: int,
				 wrapped_function: Callable = Undefined,
				 req_arg_len = Undefined) -> None:
		UnseededFunction.__init__(self, wrapped_function, req_arg_len = req_arg_len)
		NamedObj.__init__(self, name)
		self.priority = priority

	@property
	def func_name(self) -> str:
		if __debug__:
			assert len([name for name, oper in opers if self is oper]) == 1
		return next(name for name, oper in opers if self is oper)

	def __str__(self) -> str:
		return self.name

	def __repr__(self) -> str:
		return '{}({!r}, {!r}, {!r}, {!r})'.format(type(self).__qualname__,
			self.name,
			self.priority,
			await_result(self.wrapped_function),
			await_result(self.req_arg_len))

	def is_lower_precedence(self, other: UnseededFunction) -> bool:
		if not hasattr(other, 'priority'):
			return False
		return self.priority < other.priority

	async def deriv(self, du: Variable, *args: (ValuedObj, )) -> ('ValuedObj', Undefined):
		raise ValueError('What error type? TODO: find this out. But this class doesn\'t have a deriv defined')
		# return Undefined

	# def simplify(self, *args):
	# 	return None

class MultiArgOperator(Operator):
	func_for_two_args = Undefined

	def __init__(self, name: str, priority: int) -> None:
		super().__init__(name, priority, req_arg_len = -1)

	async def _reduce_args(self, *args):
		if __debug__:
			assert args, 'dont know how to deal with 0 length args yet, but its possible'
		last_res = args[0]
		for arg in args[1:]:
			last_res = self.scrub(await self.func_for_two_args(last_res, arg)) 
		return last_res
	@property
	async def wrapped_function(self):
		if __debug__:
			assert self.func_for_two_args is not Undefined
		return self._reduce_args
	# def __str__(self)

class AddSubOperator(MultiArgOperator):
	def __init__(self, name: str) -> None:
		super().__init__(name, 3)
		if __debug__:
			assert name in {'+', '-'}

	# future: async lambda 
	@staticmethod
	async def _async_lambda_plus(l, r):
		lv = future(l.value)
		rv = future(r.value)
		return await lv + await rv

	# future: async lambda 
	@staticmethod
	async def _async_lambda_minus(l, r):
		lv = future(l.value)
		rv = future(r.value)
		return await lv - await rv

	@property
	def func_for_two_args(self):
		if self._is_plus:
			return self._async_lambda_plus
		return self._async_lambda_minus

	@property
	def _is_plus(self) -> bool:
		return self.name == '+'

	async def deriv(self, du: Variable, l: ValuedObj, r: ValuedObj) -> (ValuedObj, Undefined):
		ld = future(l.deriv(du))
		rd = future(r.deriv(du))
		if self._is_plus:
			return await ld + await rd
		return await ld - await rd

class MulOperator(MultiArgOperator):
	# future: async lambda 
	@staticmethod
	async def func_for_two_args(l, r):
		lv = future(l.value)
		rv = future(r.value)
		return await lv * await rv

	# func_for_two_args = staticmethod(lambda l, r: l.value * r.value)

	def __init__(self) -> None:
		super().__init__('*', 2)

	async def deriv(self, du: Variable, l: ValuedObj, r: ValuedObj) -> (ValuedObj, Undefined):
		ld = future(l.deriv(du))
		rd = future(r.deriv(du))
		return await ld * r + l * await rd

class TrueDivOperator(MultiArgOperator):
	# future: async lambda 
	@staticmethod
	async def func_for_two_args(l, r):
		lv = future(l.value)
		rv = future(r.value)
		return await lv / await rv

	# func_for_two_args = staticmethod(lambda l, r: l.value / r.value)

	def __init__(self) -> None:
		super().__init__('/', 2)

	async def deriv(self, du: Variable, n: ValuedObj, d: ValuedObj) -> (ValuedObj, Undefined):
		nd = future(n.deriv(du))
		dd = future(d.deriv(du))
		return (d * await nd - n * await dd) / d ** 2

class PowOperator(MultiArgOperator):
	# future: async lambda
	@staticmethod
	async def func_for_two_args(b, p):
		bv = future(b.value)
		pv = future(p.value)
		return await bv ** await pv

	# func_for_two_args = staticmethod(lambda b, p: b.value ** p.value)

	def __init__(self) -> None:
		super().__init__('**', 0)

	async def _reduce_args(self, *args):
		if __debug__:
			assert args, 'dont know how to deal with 0 length args yet, but its possible'
		last_res = args[-1]
		for arg in reversed(args[:-1]):
			last_res = self.scrub(await self.func_for_two_args(arg, last_res)) 
		return last_res
		# this is different for power of, but i ahvent fixed 

	async def deriv(self, du: Variable, b: ValuedObj, p: ValuedObj) -> (ValuedObj, Undefined):
		bc = future(b.isconst(du))
		pc = future(p.isconst(du))
		bc = await bc
		pc = await pc
		if bc and pc:
			return 0

		if not bc:
			bd = future(b.deriv(du))
		if not pc:
			pd = future(p.deriv(du))
			from pymath2.extensions.functions import ln
			lnb = ln(b)

		if not bc and pc:
			return p * b ** (p - 1) * await bd
		if bc and not pc:
			return b ** p * lnb * await pd
		return b ** p * (await bd * p / b + await pd * lnb)


class InvertedOperator(Operator):
	is_inverted = True
	def __init__(self, normal_operator: Operator) -> None:
		self.normal_operator = normal_operator
		import asyncio
		super().__init__(self.normal_operator.name,
			self.normal_operator.priority,
			await_result(self.normal_operator.wrapped_function, asyncio.new_event_loop()),
			await_result(self.normal_operator.req_arg_len, asyncio.new_event_loop()))
	@property
	async def wrapped_function(self) -> Callable:
		return await self.normal_operator.wrapped_function

	@wrapped_function.setter
	async def wrapped_function(self, value) -> None:
		pass

	async def deriv(self, du: Variable, *args: [ValuedObj]) -> (ValuedObj, Undefined):
		return await self.normal_operator.deriv(du, *args[::-1]) #haha! that's how you invert it

opers = {
	'__add__': AddSubOperator('+'),
	'__sub__': AddSubOperator('-'),
	'__mul__': MulOperator(),
	'__truediv__': TrueDivOperator(),
	'__floordiv__': Operator('//', 2, lambda l, r: l.value // r.value),
	'__mod__': Operator('%', 2, lambda l, r: l.value % r.value),
	'__matmul__': Operator('@', 2, lambda l, r: l.value @ r.value),
	'__pow__': PowOperator(),

	'__and__': Operator('&', 5, lambda l, r: l.value & r.value),
	'__or__': Operator('|', 7, lambda l, r: l.value | r.value),
	'__xor__': Operator('^', 6, lambda l, r: l.value ^ r.value),
	'__lshift__': Operator('<<', 4, lambda l, r: l.value << r.value),
	'__rshift__': Operator('>>', 4, lambda l, r: l.value >> r.value),

	# '__eq__': Operator('==', lambda a, b: a == b),
	# '__ne__': Operator('', lambda l, r: l.value  r.value),
	'__lt__': Operator('<', 8, lambda l, r: l.value < r.value),
	'__gt__': Operator('>', 8, lambda l, r: l.value > r.value),
	'__le__': Operator('≤', 8, lambda l, r: l.value <= r.value),
	'__gt__': Operator('≥', 8, lambda l, r: l.value >= r.value),

	'__neg__': Operator('-', 1, lambda x: -x.value),
	'__pos__': Operator('+', 1, lambda x: +x.value),
	'__invert__': Operator('~', 1, lambda x: ~x.value),
}

opers.update({
	'__radd__': InvertedOperator(opers['__add__']),
	'__rsub__': InvertedOperator(opers['__sub__']),
	'__rmul__': InvertedOperator(opers['__mul__']),
	'__rtruediv__': InvertedOperator(opers['__truediv__']),
	'__rfloordiv__': InvertedOperator(opers['__floordiv__']),
	'__rmod__': InvertedOperator(opers['__mod__']),
	'__rmatmul__': InvertedOperator(opers['__pow__']),
	'__rpow__': InvertedOperator(opers['__pow__']),

	'__rand__': InvertedOperator(opers['__and__']),
	'__ror__': InvertedOperator(opers['__or__']),
	'__rxor__': InvertedOperator(opers['__xor__']),
	'__rlshift__': InvertedOperator(opers['__lshift__']),
	'__rrshift__': InvertedOperator(opers['__rshift__']),
})


# future: async lambda
async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv // await rv
opers['__floordiv__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv % await rv
opers['__mod__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv @ await rv
opers['__matmul__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv & await rv
opers['__and__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv | await rv
opers['__or__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv ^ await rv
opers['__xor__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv << await rv
opers['__lshift__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv >> await rv
opers['__rshift__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv < await rv
opers['__lt__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv > await rv
opers['__gt__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv <= await rv
opers['__le__'].wrapped_function = wrap_func

async def wrap_func(l, r): lv, rv = future(l.value), future(r.value); return await lv >= await rv
opers['__gt__'].wrapped_function = wrap_func


async def wrap_func(a): return -await x.value
opers['__neg__'].wrapped_function = wrap_func

async def wrap_func(a): return +await x.value
opers['__pos__'].wrapped_function = wrap_func

async def wrap_func(a): return ~await x.value
opers['__invert__'].wrapped_function = wrap_func


del wrap_func



