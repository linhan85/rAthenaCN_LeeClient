# -*- coding: utf-8 -*-

class LeeConstant:
    '''
    常量操作类
    这个类里面的所有变量只能赋值一次, 随后再也禁止赋值
    '''
    __singleInstance = None

    class ConstError(PermissionError):
        pass

    def __new__(cls):
        if cls.__singleInstance is None:
            cls.__singleInstance = object.__new__(cls)
        return cls.__singleInstance

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            raise self.ConstError("Can't rebind constant : %s" % name)
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            raise  self.ConstError("Can't unbind constant : %s" % name)
        raise  NameError(name)
