import Constants

from pubsub import pub

class PrintSubscriber:
    def __init__(self):
        pub.subscribe(self.valueChanged, Constants.VALUECHANGED_TOPIC)

    def valueChanged(self, entity):
        print(entity.dis + ' = ' + str(entity.get_value(to_string=True)))