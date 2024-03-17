def reload_package():
    package = "yourPackageName"
    import importlib
    import pkgutil

    for importer, modname, is_pkg in pkgutil.walk_packages(
        path=package.__path__, prefix=f"{package.__name__}.", onerror=lambda x: None
    ):
        try:
            module_source = importlib.import_module(modname)
            importlib.reload(module_source)
            print(f"reloaded: {modname}")
        except Exception as e:
            print(f"Could not load {modname} {e}")
