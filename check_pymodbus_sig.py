import inspect
from pymodbus.client import ModbusSerialClient

print("write_register signature:", inspect.signature(ModbusSerialClient.write_register))
print("write_registers signature:", inspect.signature(ModbusSerialClient.write_registers))
print("write_coil signature:", inspect.signature(ModbusSerialClient.write_coil))
