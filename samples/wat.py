from sync_module.model import ImplementationStatus


print(sorted({l.name for l in ImplementationStatus}))


ImplementationStatus("develop").value


def asd(_enum):

    return {
        name: _enum.__getitem__(name).value for name in sorted({l.name for l in _enum})
    }


print(asd(ImplementationStatus))
