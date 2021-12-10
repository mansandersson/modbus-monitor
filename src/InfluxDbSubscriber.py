import Constants

from datetime import datetime
from pubsub import pub
from collections import defaultdict
from influxdb import InfluxDBClient

class InfluxDbSubscriber:
    def __init__(self, host, port, user, password, db, measurement, verbose):
        pub.subscribe(self.valueChanged, Constants.VALUECHANGED_TOPIC)
        pub.subscribe(self.valueReadFinished, Constants.ITERATION_TOPIC)

        self._hasChanged = False
        self._measurement = measurement
        self._values = { }
        self._verbose = verbose
        self._ifclient = InfluxDBClient(host, port, user, password, db)
        if verbose:
            print('InfluxDb subscriber inited ...')

    def valueChanged(self, entity):
        if entity.influxdb != None:
            self._values[entity.influxdb] = entity.value
            self._hasChanged = True
    
    def valueReadFinished(self):
        if self._hasChanged == False:
            return
        self._hasChanged = False

        time = datetime.now()
        body = [
            {
                'measurement': self._measurement,
                'time': time,
                'fields': defaultdict(dict)
            }
        ]
        for key,value in self._values.items():
            body[0]['fields'][key] = value
        print(body)
        self._ifclient.write_points(body)
