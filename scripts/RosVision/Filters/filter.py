import abc
import importlib
import os
import pkgutil
from ..io_manager import IOManager

class Filter:
    __metaclass__ = abc.ABCMeta

    name = ""
    _params = None
    descriptor = None
    _io_manager = IOManager()

    def __init__(self, name, params):
        self.name = name
        self._init_params(params)
        self._init_io()

        try:
            self.initialize()
        except Exception as e:
            print 'initialize exception: %s' % e

        print "=============================="

    def _init_params(self, params):
        for p in self.descriptor.get_parameters():
            if not p.get_name() in params:
                params[p.get_name()] = p.get_default_value()
        self._params = params

    def _format_io_name(self, name):
        if name.find("/") < 0 and self.name is not None:
            name = self.name + "/" + name
        return name

    def _init_io(self):
        # Outputs
        for i in self.descriptor.get_outputs():
            if not i.get_name() in self._params:
                self._params[i.get_name()] = i.get_name()
            name = self._format_io_name(self._params[i.get_name()])
            self._io_manager.create_topic(name, i.get_io_type())

        # Inputs
        for i in self.descriptor.get_inputs():
            if not i.get_name() in self._params:
                self._params[i.get_name()] = i.get_name()
            name = self._format_io_name(self._params[i.get_name()])
            self._io_manager.watch_topic(name, i.get_io_type())


    @abc.abstractmethod
    def initialize(self):
        return

    @abc.abstractmethod
    def execute(self, time=0):
        return

    def set_param(self, name, value):
        if any(p.name == name for p in self.descriptor.get_parameters()):
            type = filter(lambda p: p.get_name() == name, self.descriptor.get_parameters())[0].get_type()
            self._params[name] = type(value)
        else:
            self._params[name] = value

        #Subscribe to the new topic
        #TODO: Unsubscribe
        for d in self.descriptor.get_outputs():
            if name == d.get_name():
                topic_name = self._format_io_name(value)
                self._io_manager.create_topic(topic_name, d.get_io_type())

        for d in self.descriptor.get_inputs():
            if name == d.get_name():
                topic_name = self._format_io_name(value)
                self._io_manager.watch_topic(topic_name, d.get_io_type())

    def get_param(self, name):
        return self._params[name]

    def get_params(self):
        return self._params

    def set_output(self, name, value):
        self._io_manager.update_value(self.get_io_name(name), value)

    def get_input(self, *names):
        topic_names = []
        for name in names:
            topic_names.append(self.get_io_name(name))
        return self._io_manager.get_values(topic_names)

    def get_io_name(self, name):
        if name in self._params:
            name = self._params[name]
        name = self._format_io_name(name)
        return name

    @staticmethod
    def list_descriptors():
        descriptors = {}
        pkgpath = os.path.dirname(os.path.realpath(__file__))

        for _, module, ispkg in pkgutil.iter_modules([pkgpath]):
            if ispkg:
                i = importlib.import_module("RosVision.Filters.%s.filter" % module)
                if hasattr(i, "__dict__"):
                    for n, c in i.__dict__.items():
                        try:
                            if issubclass(c, Filter) and n is not "Filter":
                                descriptors[n] = c.descriptor
                        except:
                            pass

        return descriptors
