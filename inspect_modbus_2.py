import inspect
from pymodbus.client import ModbusSerialClient

with open("sig_dump.txt", "w") as f:
    try:
        sig = inspect.signature(ModbusSerialClient.write_register)
        f.write(str(sig) + "\n")
        f.write("Params:\n")
        for name, param in sig.parameters.items():
            f.write(f"{name}: {param.kind}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
