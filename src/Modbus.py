import serial
from pymodbus.client.sync import ModbusSerialClient
import pymodbus.exceptions
import RPi.GPIO as GPIO
from enum import Enum

class ModbusRegister(Enum):
    UNKNOWN = 0
    INPUT = 1
    HOLDING = 2
    def __str__(self):
        return self.name

class ModbusReadMessage:
    def __init__(self, reg_type, start, count):
        self.reg_type = reg_type
        self.start = start
        self.count = count

    def __str__(self):
        return 'Start at {} register {} and read {} registers'.format(self.reg_type,
                                                                      self.start,
                                                                      self.count)

class ModbusClient:
    def __init__(self, port, slave_addr):
        # Configure GPIO pin
        EN_485 =  4
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(EN_485, GPIO.OUT)
        GPIO.output(EN_485, GPIO.HIGH)

        # Initialize Modbus serial client
        self.slave_addr = slave_addr
        self.client = ModbusSerialClient(method='rtu',
                                         port=port,
                                         baudrate=115200,
                                         bytesize=serial.EIGHTBITS,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE)
        self.client.connect()
    
    def __del__(self):
        self.client.close()
    
    def read_input_registers(self, start_reg, count):
        return self.client.read_input_registers(start_reg, count, unit=self.slave_addr)
    
    def read_holding_registers(self, start_reg, count):
        return self.client.read_holding_registers(start_reg, count, unit=self.slave_addr)