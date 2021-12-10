import Constants

from pubsub import pub

class PrintSubscriber:
    def __init__(self, verbose):
        pub.subscribe(self.valueChanged, Constants.VALUECHANGED_TOPIC)
        if verbose:
            print('Print subscriber inited ...')

    def valueChanged(self, entity):
        print(entity.dis + ' = ' + str(entity.get_value(to_string=True)))