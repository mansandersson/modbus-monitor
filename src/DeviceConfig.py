from enum import Enum
from Modbus import ModbusReadMessage, ModbusRegister

class EntityType(Enum):
    UNKNOWN = 0
    EQUIP = 1
    POINT = 2
    def __str__(self):
        return self.name

class Entity:
    def __init__(self, type, id, dis, reg_type, reg_id):
        self.type = type
        self.id = id
        self.dis = dis
        self.modbus_reg_type = reg_type
        self.modbus_reg_id = reg_id

    def __str__(self):
        return '{} Entity (id:{})(dis:{})(modbus:{}{})'.format(self.type,
                                                               self.id,
                                                               self.dis,
                                                               self.modbus_reg_type,
                                                               self.modbus_reg_id)

class DeviceConfig:
    """Device Configuration class

    Attributes:
      path: Path to the device configuration file
      holding_regs: List of entities using modbus holding registers
      input_regs: List of entities using modbus input registers
      verbose: Whether to enable verbose output
    """
    def __init__(self, path, verbose=False):
        """Sets up the class and parses the configuration file.

        Args:
          path:
            Path to the device configuration file (string)
          verbose:
            Whether to enable verbose output for operations in this
            class (boolean)
        """
        self.path = path
        self.holding_regs = { }
        self.input_regs = { }
        self.verbose = verbose

        self.__parse()

    def __parse(self):
        """Parse a device config file and build a model of the device

        Format of the device configuration should be the Trio format of
        Project Haystack (https://project-haystack.org/) but with some
        extra additions in terms of tags to better define the data and
        how to read it.
        """
        file = open(self.path, 'r')
        line_count = 0

        type = EntityType.UNKNOWN
        id = None
        dis = ''
        reg_type = ModbusRegister.UNKNOWN
        reg_id = None
        trio = ''
        error = False
        while True:
            line_count += 1

            line = file.readline()
            if not line:
                break
            elif line.startswith('//'):
                continue
            elif line.startswith('-'):
                if (
                        id != None and
                        error == False and
                        (type == EntityType.EQUIP or type == EntityType.POINT) and
                        reg_type != ModbusRegister.UNKNOWN and
                        reg_id != None
                    ):
                    entity = Entity(type, id, dis, reg_type, reg_id)
                    if self.verbose:
                        print('Found {}'.format(entity))

                    if reg_type == ModbusRegister.HOLDING:
                        self.holding_regs[reg_id] = entity
                    elif reg_type == ModbusRegister.INPUT:
                        self.input_regs[reg_id] = entity
                    else:
                        print('Error: Invalid modbus register type (entity ending at line {})'.format(line_count))

                # new entity, clean out
                type = EntityType.UNKNOWN
                id = None
                dis = ''
                reg_type = ModbusRegister.UNKNOWN
                reg_id = None
                trio = ''
                error = False
            else:
                trio += '\n' + line.strip()
                parts = line.split(':')
                if len(parts) == 2:
                    tag_name = parts[0].strip()
                    tag_value = parts[1].strip()
                    if tag_name == 'id':
                        id = tag_value
                    elif tag_name == 'dis':
                        dis = tag_value.strip('"')
                    elif tag_name == 'modbusInputReg':
                        reg_type = ModbusRegister.INPUT
                        reg_id = int(tag_value)
                    elif tag_name == 'modbusHoldingReg':
                        reg_type = ModbusRegister.HOLDING
                        reg_id = int(tag_value)
                elif len(parts) == 1:
                    tag_name = parts[0].strip()
                    if tag_name == 'equip':
                        type = EntityType.EQUIP
                    elif tag_name == 'point':
                        type = EntityType.POINT
                else:
                    error = True
                    print('Error: Invalid line in Device Config file ({})'.format(line_count))
    
    def __build_modbus_messages(self, entities):
        """Builds modbus messages based on the entities supplied as args

        Builds a list of modbus messages that needs to be sent to retrieve
        all data for the entities supplied to the method.

        Args:
          entities:
            List of entities to build modbus messages for. It is expected
            that all entities are using the same type of Modbus register.
        
        Returns:
          List of objects of ModbusReadMessage type
        """
        messages = [ ]
        regs = list(entities.keys())
        regs.sort()

        start_id = None
        last_id = None
        count = 0
        for id in regs:
            if start_id == None:
                # Start a new message
                start_id = id
                last_id = id
                count = 1
            elif last_id + 1 == id:
                # Add to same message
                last_id = id
                count += 1
            elif last_id + 1 != id:
                # Save current message
                if start_id != None:
                    messages.append(ModbusReadMessage(ModbusRegister.INPUT, start_id, count))
                start_id = id
                last_id = id
                count = 1
            elif count == 124:
                # We've reached maximum number of registers to read at once
                # Save current message
                count += 1
                if start_id != None:
                    messages.append(ModbusReadMessage(ModbusRegister.INPUT, start_id, count))
                start_id = id
                last_id = id
                count = 1
            else:
                # Error, shouldn't end up here
                print('Error: Unknown error')
        # Save last message
        if start_id != None:
            messages.append(ModbusReadMessage(ModbusRegister.INPUT, start_id, count))
        return messages

    def get_modbus_messages(self):
        """Fetches a list of modbus messages to send to get all device data

        Builds a list of modbus messages that needs to be sent to retrieve
        all data for the device. To minimize modbus traffic it will try to
        combine reading of multiple registers so that as few messages as
        possible are being sent.

        Returns:
          List of objects of ModbusReadMessage type
        """
        messages = [ ]

        messages.extend(self.__build_modbus_messages(self.input_regs))
        messages.extend(self.__build_modbus_messages(self.holding_regs))

        return messages
    
    def get_entity(self, reg_type, reg_id):
        """Fetches an entity based on its modbus configuration

        Retrieves an entity object pertaining to the given arguments
        supplied to the method.
        
        Args:
          reg_type:
            Modbus register type (enum ModbusRegister)
          reg_id:
            Modbus register id / address
        
        Returns:
          An Entity object, or None if none were found
        """
        if reg_type == ModbusRegister.INPUT:
            return self.input_regs[reg_id]
        elif reg_type == ModbusRegister.HOLDING:
            return self.holding_regs[reg_id]
        else:
            return None
