#!/usr/bin/env python3
from DeviceConfig import DeviceConfig
from Modbus import ModbusClient, ModbusReadMessage, ModbusRegister
import sys
import getopt

def print_help():
    print('main.py -d <device-config-file>')

def main(argv):
    # Default configuration values
    device_config_path = None
    verbose = False

    # Get command-line options
    try:
        opts, args = getopt.getopt(argv, 'hd:v', ['help', 'device-config=', 'verbose'])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_help()
            sys.exit()
        elif opt in ('-d', '--device-config'):
            device_config_path = arg
        elif opt in ('-v', '--verbose'):
            verbose = True

    # Check that configuration is valid
    if device_config_path == None:
        print('Error: no device config path configured')
        sys.exit(1)

    # Print configuration if verbose mode
    if verbose:
        print('--------------')
        print('Configuration:')
        print('    Device Config File: {}'.format(device_config_path))
        print('--------------')

    # Load the Device Config file
    dc = DeviceConfig(device_config_path, verbose=verbose)

    # Initialize Modbus Client
    modbus = ModbusClient('/dev/ttyS0', 1)

    # Get a list of Modbus messages and execute them
    messages = dc.get_modbus_messages()
    for message in messages:
        response = None
        if message.reg_type == ModbusRegister.INPUT:
            response = modbus.read_input_registers(message.start, message.count)
        elif message.reg_type == ModbusRegister.HOLDING:
            response = modbus.read_holding_registers(message.start, message.count)
        else:
            print('Error: Unknown modbus register type')
        
        if response.isError():
            print(rr.error())
        else:
            reg_id = message.start
            for reg_value in response.registers:
                entity = dc.get_entity(message.reg_type, reg_id)

                print(entity.dis + ' = ' + str(reg_value))
                reg_id += 1

if __name__ == '__main__':
    main(sys.argv[1:])
