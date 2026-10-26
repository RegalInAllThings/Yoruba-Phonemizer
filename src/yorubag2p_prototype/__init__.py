"""Load optional rule dependencies only when their converters are requested."""
def __getattr__(name):
    if name == 'NeuralConverter':
        from .neural import NeuralConverter
        return NeuralConverter
    if name == 'YorubaConverter':
        from .converter import YorubaConverter
        return YorubaConverter
    if name == 'HybridConverter':
        from .hybrid import HybridConverter
        return HybridConverter
    raise AttributeError(name)
