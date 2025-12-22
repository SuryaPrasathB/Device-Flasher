import serial.tools.list_ports
from app.utils.logger import logger

class PortScanner:
    @staticmethod
    def get_available_ports():
        """
        Returns a list of available COM ports.
        Each item is a dictionary with 'port', 'description', 'hwid'.
        """
        ports = serial.tools.list_ports.comports()
        available_ports = []
        for port in ports:
            port_info = {
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid
            }
            available_ports.append(port_info)
        
        logger.debug(f"Found ports: {available_ports}")
        return available_ports
