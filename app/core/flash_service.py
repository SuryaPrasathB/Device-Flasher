import time
from app.modbus.modbus_client import ModbusClientWrapper
from app.utils.config import config
from app.utils.logger import logger

class FlashService:
    def __init__(self):
        self.modbus_client = ModbusClientWrapper()
        
    def flash_device(self, port, new_slave_id, progress_callback=None):
        """
        Executes the flashing sequence.
        
        Args:
            port (str): The COM port to connect to.
            new_slave_id (int): The new Slave ID to assign.
            progress_callback (func): Optional callback(message, percent) for UI updates.
            
        Returns:
            bool: True if success, False otherwise.
            str: Message detailing the result.
        """
        
        def update_progress(msg, pct):
            if progress_callback:
                progress_callback(msg, pct)
            logger.info(msg)

        # 1. Connect
        update_progress(f"Connecting to {port}...", 10)
        if not self.modbus_client.connect(port):
            return False, "Failed to connect to serial port."

        try:
            # Load Config Addresses
            reg_map = config.register_map
            id_reg_addr = reg_map.get("slave_id_register_address", 0)
            update_coil_addr = reg_map.get("slave_id_set_coil", 0)
            setting_mode_coil_addr = reg_map.get("slave_id_setting_mode_coil", 0)
            
            # Broadcast ID is always 0
            BROADCAST_ID = 0
            
            # 2. Write New Slave ID
            update_progress(f"Broadcasting New ID {new_slave_id} to Register {id_reg_addr}...", 30)
            
            # Broadcast ID
            logger.info(f"Broadcast ID")
            self.modbus_client.write_register(BROADCAST_ID, id_reg_addr, int(new_slave_id))
            time.sleep(0.01)
            
            time.sleep(0.5) # Short grace period

            # 3. Trigger SLAVE_ID_SETTING_MODE Coil
            update_progress(f"Triggering SLAVE_ID_SETTING_MODE Coil {setting_mode_coil_addr}...", 50)
            logger.info(f"Broadcast Setting Mode Coil")
            self.modbus_client.write_coil(BROADCAST_ID, setting_mode_coil_addr, True)
            time.sleep(0.1)

            # 4. Write Update Coil
            update_progress(f"Triggering Update Coil {update_coil_addr}...", 80)
            
            # Broadcast Coil
            logger.info(f"Broadcast Coil")
            self.modbus_client.write_coil(BROADCAST_ID, update_coil_addr, True)
            time.sleep(0.01)

            # 5. Finish
            # We assume success as per instructions to just broadcast and complete.
            update_progress("Broadcast complete.", 100)
            return True, f"Broadcasted New ID {new_slave_id}."

        except Exception as e:
            return False, f"Unexpected error during flash: {e}"
        finally:
            self.modbus_client.disconnect()
