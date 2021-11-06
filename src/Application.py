#!/usr/bin/env python3
from DeviceConfig import DeviceConfig
from Modbus import ModbusClient, ModbusReadMessage, ModbusRegister
from configparser import ConfigParser, NoOptionError, NoSectionError
import getopt
import sched
import sys
import time

class ConfigFile:
    def __init__(self, config_path):
        self._config = ConfigParser()
        self._config.read(config_path)

    def get_setting(self, section, config):
        try:
            ret = self._config.get(section, config)
        except NoOptionError:
            ret = None
        except NoSectionError:
            ret = None
        if ret == 'True':
            ret = True
        elif ret == 'False':
            ret = False
        return ret

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
        self.config_path = '/etc/modbus-monitor.conf'
        self.device_config_path = None
        self.serial_device = None
        self.slave_addr = None
        self.verbose = False

        # Get command-line options
        try:
            opts, args = getopt.getopt(argv, 'ha:c:d:s:v', ['help', 'config=', 'device-config=', 'slave-address=', 'serial-device=', 'verbose'])
        except getopt.GetoptError:
            self.print_help()
            sys.exit(2)
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.print_help()
                sys.exit()
            elif opt in ('-a', '--slave-address'):
                self.slave_addr = int(arg)
            elif opt in ('-c', '--config'):
                self.config_path = arg
            elif opt in ('-d', '--device-config'):
                self.device_config_path = arg
            elif opt in ('-s', '--serial-device'):
                self.serial_device = arg
            elif opt in ('-v', '--verbose'):
                self.verbose = True

        # Get ini-file options
        try:
            config = ConfigFile(self.config_path)
        except:
            print('Error: unable to read config file (' + self.config_path + ')')
            sys.exit(3)
        
        if self.device_config_path == None and config.get_setting('device', 'config') != None:
            self.device_config_path = config.get_setting('device', 'config')
        if self.slave_addr == None and config.get_setting('modbus', 'address') != None:
            self.slave_addr = int(config.get_setting('modbus', 'address'))
        if self.serial_device == None and config.get_setting('modbus', 'serial') != None:
            self.serial_device = config.get_setting('modbus', 'serial')
        
        # Check that configuration is valid
        if self.device_config_path == None:
            print('Error: no device config path configured')
            sys.exit(1)

        if self.slave_addr == None:
            print('Error: no modbus slave address configured')
            sys.exit(1)
        
        if self.serial_device == None:
            print('Error: no modbus serial device configured')
            sys.exit(1)

        # Print configuration if verbose mode
        if self.verbose:
            print('--------------')
            print('Configuration:')
            print('    Device Config File: {}'.format(self.device_config_path))
            print('    Modbus Address: {}'.format(self.slave_addr))
            print('    Modbus Device: {}'.format(self.serial_device))
            print('--------------')

        # Load the Device Config file
        self._config = DeviceConfig(self.device_config_path, verbose=self.verbose)

        # Initialize Modbus
        self._modbus = ModbusClient(self.serial_device, self.slave_addr)
        self._modbus_messages = self._config.get_modbus_messages()

        # Set up scheduler
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._starttime = time.time()
        self._schedule(1, 1, self._event_read_modbus)
    
    def print_help(self):
        """Print application's help text
        """
        print('{} [options]'.format(self.app_name))
        print('    -a / --slave-address=')
        print('        Modbus Slave Address (decimal integer)')
        print('    -c / --config=')
        print('        Path to config file for application')
        print('    -d / --device-config=')
        print('        Path to device config (.trio) that describe device being monitored')
        print('    -h / --help')
        print('        Shows this help text')
        print('    -s / --serial-device=')
        print('        Serial device to use for Modbus communication')
        print('    -v / --verbose=')
        print('        Verbose output from application')
    
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
                    entity.set_value(reg_value)

                    print(entity.dis + ' = ' + str(entity.get_value(to_string=True)))
                    reg_id += 1
        
        # Reschedule this function
        self._schedule(1, 1, self._event_read_modbus)