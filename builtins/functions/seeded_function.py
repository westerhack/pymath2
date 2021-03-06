from typing import Any

from . import logger

from pymath2 import Undefined, override, finish, iscoroutine, warnloop, inloop

from pymath2.builtins.variable import Variable
from pymath2.builtins.operable import Operable
from pymath2.builtins.derivable import Derivable

from pymath2.builtins.objs.valued_obj import ValuedObj
from pymath2.builtins.objs.named_valued_obj import NamedValuedObj

class SeededFunction(NamedValuedObj, Derivable):

	@override(NamedValuedObj)
	async def __ainit__(self, unseeded_base_object: 'UnseededFunction', args: tuple = Undefined, **kwargs) -> None:
		warnloop(logger)
		assert inloop()
		if __debug__:
			from .unseeded_function import UnseededFunction
			assert isinstance(unseeded_base_object, UnseededFunction), '{}, type {}'.format(unseeded_base_object, type(unseeded_base_object))
		async with finish() as f:
			f.future(super().__ainit__(**kwargs))
			f.future(self.__asetattr__('unseeded_base_object', unseeded_base_object))
			f.future(self.__asetattr__('args', args))
		assert hasattr(self, 'unseeded_base_object')
		assert hasattr(self, 'args')
	@property
	async def _args_str(self):
		warnloop(logger)
		assert inloop()
		ret = []
		async with finish() as f:
			for x in (f.future(arg) for arg in self.args):
				ret.append(arg)
		return str([x.result() for x in ret])

	@override(NamedValuedObj)
	@property
	async def _aname(self):
		warnloop(logger)
		assert inloop()
		if self._name is Undefined:
			return await self.unseeded_base_object._aname
		else:
			assert self._name is not Undefined
			return self.name

	###
	def get_vars(self):
		warnloop(logger) #idk if this is necessary
		assert inloop() #idk if this is necessary
		ret = []
		for arg in self.args:
			if isinstance(arg, SeededFunction):
				logger.debug('Append get_vars from SeededFunction at 0x{:0x}'.format(id(arg)))
					# cause cant call str cause might be in loop
				ret += arg.get_vars()
			elif isinstance(arg, Variable):
				logger.debug('Append get_vars from Variable at 0x{:0x}'.format(id(arg)))
					# cause cant call str cause might be in loop
				ret.append(arg)
		return ret
	###


	@override(NamedValuedObj)
	@property
	async def _avalue(self) -> Any:
		func = await self.unseeded_base_object._afunc


		# disable_complete()

		# else:
		# print('argstr:', await self._args_str)
		assert not hasattr(func, '__aiter__')

		res = func(*self.args)
		# enable_complete()
		# this is badddddd
		while iscoroutine(res):
			res = await res
		assert not iscoroutine(res)

		scrubbed = await self.scrub(res)
		assert not iscoroutine(scrubbed)
		return scrubbed

	@override(NamedValuedObj)
	@property
	async def _ahasvalue(self) -> Any:
		selfv = await self._avalue
		hasv = await selfv._ahasvalue
		return hasv
		return await (await self._avalue)._ahasvalue #double await

	@override(NamedValuedObj)
	async def __astr__(self) -> str:
		if await self._ahasvalue:
			return await (await self._avalue).__astr__()
		async with finish() as f:
			name = f.future(self._aname)
			primestr = f.future(self.unseeded_base_object._aprime_str(self.unseeded_base_object.deriv_num))
			if self.args is Undefined:
				args = f.future(self.args.__astr__())
			else:
				args = []
				for arg in (f.future(x.__astr__()) for x in self.args):
					args.append(await arg)
				args = ', '.join(args)
			return '{}{}({})'.format(await name, await primestr, args)

	@override(NamedValuedObj)
	async def __arepr__(self) -> str:
		async with finish() as f:
			baseobj = f.future(self.unseeded_base_object.__arepr__())
			hasname = f.future(self._ahasname)
			name = f.future(self._aname)
			args = ', {}'.format(await self.get_asyncattr(args)) if self.args is not Undefined else ''
			return '{}({}{}{})'.format(self.__class__.__name__, await baseobj, args, await name if await hasname else '')

	@override(Derivable)
	async def _aisconst(self, du):
		return await self._ahasvalue #await #maybe something with du? 


	# def deriv(self, du: Variable) -> 'SeededFunction':
	# 	derviative = (self.value)._aderiv(du)
	# 	print(derviative)
	# 	quit()


	@staticmethod
	async def _gen_wrapped_func(val, du):
		deriv = await (val._aderiv(du))
		# print(deriv)
		# b = deriv.unseeded_base_object.func
		# print(b)
		# quit()
		# def y(): pass
		# import types
		# yc = y.__code__
		# y_code = types.CodeType(deriv.unseeded_base_object.req_arg_len, 0,
		#             yc.co_nlocals,
		#             yc.co_stacksize,
		#             yc.co_flags,
		#             yc.co_code,
		#             yc.co_consts,
		#             yc.co_names,
		#             yc.co_varnames,
		#             yc.co_filename,
		#             'f',
		#             yc.co_firstlineno,
		#             yc.co_lnotab)
		# print('I\'m here')

		# return types.FunctionType(y_code, y.__globals__, 'f')
		return await deriv

	@override(Derivable)
	async def _aderiv(self, du: Variable) -> 'UnseededFunction':
		from .unseeded_function import UnseededFunction


		req_arg_len = self.unseeded_base_object.req_arg_len #ensure_future
		func = await self._gen_wrapped_func(await self._avalue, du)
		func_str = str(func)
		uns_func =  UnseededFunction(
							  func = lambda *args: func(*args), #await
						      name = self.name,
						      deriv_num = self.unseeded_base_object.deriv_num + 1,
						      req_arg_len = req_arg_len, #await
						      args_str = self.unseeded_base_object.args_str,
						      body_str = func_str)
		return uns_func
		# print(derived_function)
	@override(Derivable)
	async def _aderiv(self, du: Variable) -> 'SeededFunction':
		ret = await (await self._avalue)._aderiv(du)
		from pymath2.builtins.objs.math_obj import MathObj
		assert isinstance(ret, MathObj)
		return ret



	async def copy(self):
		args = []
		for arg in self.args:
			if hasattr(arg, 'copy'):
				args.append(await arg.copy())
			else:
				args.append(arg)
		return await type(self).__anew__(type(self),
					 unseeded_base_object = self.unseeded_base_object,
					 args = args)


	def _new_result_replace(self, args):
		args = self._map_args_to_my_args(args)
		self._new_result_replace_wrapped(args)
	def _new_result_replace_wrapped(self, passedargs):
		res = []
		for myarg in self.args:
			if isinstance(myarg, SeededFunction):
				myarg._new_result_replace_wrapped(passedargs)
				res.append(myarg)
				continue
			for myarg1, passedarg in passedargs:
				if myarg is myarg1:
					res.append(passedarg)
					break
			else:
				res.append(myarg)
				assert not isinstance(myarg, Variable) and myarg is not None, str(myarg)
			# assert myarg args, 'a'
		assert all(x is not None for x in res), res
		self.args = res

	def _map_args_to_my_args(self, args):
		a = list(zip(self.get_vars(), args))
		return a
