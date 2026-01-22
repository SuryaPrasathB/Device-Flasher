import inspect
from pymodbus.client import ModbusSerialClient

print("Inspecting ModbusSerialClient.write_register:")
try:
    print(inspect.signature(ModbusSerialClient.write_register))
except Exception as e:
    print(f"Error inspecting ModbusSerialClient: {e}")

try:
    # also check instance method
    client = ModbusSerialClient(port="COM1")
    print(inspect.signature(client.write_register))
except Exception as e:
    print(e)
