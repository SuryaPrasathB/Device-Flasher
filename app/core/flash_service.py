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
            update_coil_addr = reg_map.get("update_coil_address", 0)
            
            # Broadcast ID is always 0
            BROADCAST_ID = 0
            
            # 2. Write New Slave ID
            update_progress(f"Writing New ID {new_slave_id} to Register {id_reg_addr} (Broadcast)...", 30)
            success, error = self.modbus_client.write_register(BROADCAST_ID, id_reg_addr, int(new_slave_id))
            
            # Note: Write to broadcast usually returns no response. 
            # pymodbus client might timeout waiting for it, or return success if it just sent.
            # If it returns error due to timeout (expected for broadcast), we should proceed carefully.
            # However, usually Modbus libraries allow setting 'broadcast=True' or we just ignore the timeout if we know it's broadcast.
            # In pymodbus, if we send to unit 0, it might still wait. 
            # If we get a timeout, we treat it as "Command Sent" for broadcast.
            
            if not success:
                # If error is specifically "No Response" or "Timeout" on Broadcast, it might be actually fine.
                # But safer to fail unless we are sure.
                # Let's assume for now we need strict success. 
                # If the device is non-standard and replies, we are good.
                # If it is standard and doesn't reply, we might see a timeout.
                # User Requirement: "Wait for Modbus response OR Timeout".
                # If timeout happens on broadcast, we proceed to next step?
                # User said: "Wait for: Valid Modbus response OR Timeout". 
                # This implies timeout is an acceptable state to proceed or check?
                # No, usually "Wait for valid response OR timeout" means "Stop waiting if timeout occurs".
                # But does it mean "Fail"? 
                # User said: "Handle: CRC errors, No response".
                # If "No response" -> Handle it.
                # But for Broadcast, "No response" is success.
                # I will log warning on timeout but proceed for Broadcast operations.
                if "Timeout" in str(error) or "No Response" in str(error):
                    logger.warning("Broadcast write timed out (expected for standard Modbus). Proceeding.")
                else:
                    return False, f"Failed to write Slave ID: {error}"
            
            time.sleep(0.5) # Short grace period

            # 3. Write Update Coil
            update_progress(f"Triggering Update Coil {update_coil_addr}...", 60)
            success, error = self.modbus_client.write_coil(BROADCAST_ID, update_coil_addr, True)
            
            if not success:
                 if "Timeout" in str(error) or "No Response" in str(error):
                    logger.warning("Broadcast coil write timed out (expected). Proceeding.")
                 else:
                    return False, f"Failed to trigger Update Coil: {error}"

            # 4. Wait / Verify
            # User sequence: "Wait for Modbus response / confirmation".
            # Since we likely timed out above or got a response, we are effectively done with the "write" part.
            # The "confirmation" ideally comes from verifying the new ID.
            
            update_progress("Verifying new settings...", 80)
            time.sleep(1.0) # Wait for device to apply settings
            
            # OPTIONAL: Try to ping the new Slave ID.
            # This gives us the "Absolute Certainty" the user requested implicitly by "Display success or error status".
            # If we just broadcast and say "Success", we lied if the device didn't pick it up.
            # I will attempt to read the ID register back using the NEW ID.
            
            read_vals, error = self.modbus_client.read_holding_registers(new_slave_id, id_reg_addr, 1)
            
            if read_vals and len(read_vals) > 0:
                # If we read it back, great.
                # Optionally check if read_vals[0] == new_slave_id (it should be).
                if read_vals[0] == new_slave_id:
                     update_progress("Verification Successful.", 100)
                     return True, f"Successfully flashed Slave ID {new_slave_id}."
                else:
                     return False, f"Verification failed. Read ID {read_vals[0]} but expected {new_slave_id}."
            else:
                # If verification fails (timeout), it might be because the device is rebooting or slow.
                # But we must report what happened.
                return False, f"Could not verify new Slave ID. Device may be unresponsive or ID not set. Error: {error}"

        except Exception as e:
            return False, f"Unexpected error during flash: {e}"
        finally:
            self.modbus_client.disconnect()
