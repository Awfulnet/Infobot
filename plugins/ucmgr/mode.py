from .meta import TypePreserving, StringSet

class ModeSet(StringSet, TypePreserving):
    """ A set of IRC modes. """
    def __repr__(self):
        if len(self) == 0:
            return '<no modes>'

        long_modes = dict(mode.split() for mode in self if len(mode) > 1)
        normal_modes = ''.join(mode for mode in self if len(mode) == 1)
        if long_modes:
            return f"+{normal_modes}{''.join(long_modes)} {' '.join(long_modes.values())}"
        else:
            return f"+{normal_modes}"


