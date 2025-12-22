from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from app.utils.logger import logger
from app.utils.config import config

class ModbusClientWrapper:
    def __init__(self):
        self.client = None
        self.connected = False
        self._load_settings()

    def _load_settings(self):
        settings = config.modbus_settings
        self.baudrate = settings.get("baudrate", 9600)
        self.bytesize = settings.get("bytesize", 8)
        self.parity = settings.get("parity", "N")
        self.stopbits = settings.get("stopbits", 1)
        self.timeout = settings.get("timeout", 1)
        # retries handled by pymodbus or custom logic? pymodbus has retries.

    def connect(self, port):
        """
        Connects to the specified serial port.
        """
        logger.info(f"Connecting to {port} with baud={self.baudrate}, parity={self.parity}...")
        
        try:
            self.client = ModbusSerialClient(
                port=port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            
            self.connected = self.client.connect()
            if self.connected:
                logger.info("Connection successful.")
                return True
            else:
                logger.error("Failed to connect to port.")
                return False
        except Exception as e:
            logger.error(f"Connection exception: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """
        Closes the serial connection.
        """
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected.")

    def write_register(self, slave_id, address, value):
        """
        Writes a single holding register.
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Modbus device.")

        logger.debug(f"Writing Register: ID={slave_id}, Addr={address}, Val={value}")
        try:
            # pymodbus write_register(address, value, device_id=slave_id)
            response = self.client.write_register(address, value, device_id=slave_id)
            
            if response.isError():
                logger.error(f"Modbus Error (Write Register): {response}")
                return False, str(response)
            
            return True, None
        except ModbusException as e:
            logger.error(f"Modbus Exception (Write Register): {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"General Exception (Write Register): {e}")
            return False, str(e)

    def write_coil(self, slave_id, address, value):
        """
        Writes a single coil.
        """
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Modbus device.")

        logger.debug(f"Writing Coil: ID={slave_id}, Addr={address}, Val={value}")
        try:
            # pymodbus write_coil(address, value, device_id=slave_id)
            response = self.client.write_coil(address, value, device_id=slave_id)
            
            if response.isError():
                logger.error(f"Modbus Error (Write Coil): {response}")
                return False, str(response)
            
            return True, None
        except ModbusException as e:
            logger.error(f"Modbus Exception (Write Coil): {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"General Exception (Write Coil): {e}")
            return False, str(e)
            
    def read_holding_registers(self, slave_id, address, count=1):
        """
        Reads holding registers. Useful for verification.
        """
        if not self.connected or not self.client:
             raise ConnectionError("Not connected to Modbus device.")
             
        logger.debug(f"Reading Registers: ID={slave_id}, Addr={address}, Count={count}")
        try:
            response = self.client.read_holding_registers(address, count=count, device_id=slave_id)
            if response.isError():
                logger.error(f"Modbus Error (Read Register): {response}")
                return None, str(response)
            return response.registers, None
        except Exception as e:
            logger.error(f"Exception (Read Register): {e}")
            return None, str(e)
