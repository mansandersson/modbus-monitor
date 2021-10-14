#!/usr/bin/env python3
from DeviceConfig import DeviceConfig
from Modbus import ModbusClient, ModbusReadMessage, ModbusRegister
import getopt
import sched
import sys
import time

class Application:
    """Application class

    Attributes:
      app_name: Name of the executable running
      device_config_path: Path to the device config
      verbose: Whether verbose output is enabled
      _config: DeviceConfig instance used by application
      _modbus: ModbusClient instance used by application
      _modbus_messages: List of Modbus messages to send on every iteration
      _scheduler: Scheduler instance used by application
      _starttime: Start time of application.
    """
    def __init__(self, app_name, argv):
        """Parses input arguments and sets up the application

        Args:
          app_name:
            Name of the application executable
          argv:
            Arguments supplied to the application
        """
        # Default configuration values
        self.app_name = app_name
        self.device_config_path = None
        self.verbose = False

        # Get command-line options
        try:
            opts, args = getopt.getopt(argv, 'hd:v', ['help', 'device-config=', 'verbose'])
        except getopt.GetoptError:
            self.print_help()
            sys.exit(2)
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.print_help()
                sys.exit()
            elif opt in ('-d', '--device-config'):
                self.device_config_path = arg
            elif opt in ('-v', '--verbose'):
                self.verbose = True

        # Check that configuration is valid
        if self.device_config_path == None:
            print('Error: no device config path configured')
            sys.exit(1)

        # Print configuration if verbose mode
        if self.verbose:
            print('--------------')
            print('Configuration:')
            print('    Device Config File: {}'.format(device_config_path))
            print('--------------')

        # Load the Device Config file
        self._config = DeviceConfig(self.device_config_path, verbose=self.verbose)

        # Initialize Modbus
        self._modbus = ModbusClient('/dev/ttyS0', 1)
        self._modbus_messages = self._config.get_modbus_messages()

        # Set up scheduler
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._starttime = time.time()
        self._schedule(1, 1, self._event_read_modbus)
    
    def print_help(self):
        """Print application's help text
        """
        print('{} -d <device-config-file>'.format(self.app_name))
    
    def _schedule(self, interval, priority, action, argument=(), kwargs={}):
        """Schedule an event to happen at a certain interval

        Makes sure that the interval is kept by taking into account
        the actual time for execution of the event.

        Args:
          interval:
            Interval in seconds
          priority:
            Priority of the event. Events scheduled at same time
            will execute in order of priority.
          action:
            Method to run when event is fired
          argument:
            Arguments to supply to the method
          kwargs:
            Arguments to supply to the method
        """
        now = time.time()
        next = now + (interval - ((now - self._starttime) % interval))
        self._scheduler.enterabs(next, priority, action, argument, kwargs)

    def run(self):
        """Runs the application
        """
        self._scheduler.run()

    def _event_read_modbus(self):
        """Event for reading data over Modbus

        Loops through all Modbus messages needed to read the device
        data and prints the received data.
        """
        for message in self._modbus_messages:
            response = None
            if message.reg_type == ModbusRegister.INPUT:
                response = self._modbus.read_input_registers(message.start, message.count)
            elif message.reg_type == ModbusRegister.HOLDING:
                response = self._modbus.read_holding_registers(message.start, message.count)
            else:
                print('Error: Unknown modbus register type')
            
            if response.isError():
                print(rr.error())
            else:
                reg_id = message.start
                for reg_value in response.registers:
                    entity = self._config.get_entity(message.reg_type, reg_id)

                    print(entity.dis + ' = ' + str(reg_value))
                    reg_id += 1
        
        # Reschedule this function
        self._schedule(1, 1, self._event_read_modbus)