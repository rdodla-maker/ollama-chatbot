import importlib.util
spec = importlib.util.spec_from_file_location('calc','backend/tools/calculator.py')
calc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc)
print('safe_calculate 2+2 ->', calc.safe_calculate('2+2'))
print('calculator_tool ->', calc.calculator_tool('What is 10 / 4'))
