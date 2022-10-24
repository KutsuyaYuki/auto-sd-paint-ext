from dataclasses import asdict
from typing import Any

from krita import QObject, QReadWriteLock, QSettings

from .defaults import CFG_FOLDER, CFG_NAME, DEFAULTS


class Config(QObject):
    def __init__(self, folder=CFG_FOLDER, name=CFG_NAME, model=DEFAULTS):
        """Sorta like a controller for QSettings.

        I'm going to treat this as a singleton global app state, but implemented
        correctly such that it should be theoretically possible to have multiple
        instances (maybe multiple dockers controlling multiple remotes?)

        Args:
            folder (str, optional): Which folder to store settings in. Defaults to CFG_FOLDER.
            name (str, optional): Name of settings file. Defaults to CFG_NAME.
            model (Any, optional): Data model representing config & defaults. Defaults to DEFAULTS.
        """
        # See: https://doc.qt.io/qt-6/qsettings.html#accessing-settings-from-multiple-threads-or-processes-simultaneously
        # but im too lazy to figure out creating separate QSettings per worker, so we will just lock
        self.model = model
        self.lock = QReadWriteLock()
        self.config = QSettings(QSettings.IniFormat, QSettings.UserScope, folder, name)

        # add in new config settings
        self.restore_defaults(overwrite=False)

    def __call__(self, key: str, type: type = str):
        """Shorthand for Config.get()"""
        return self.get(key, type)

    def get(self, key: str, type: type = str):
        """Get config value by key & cast to type.

        Args:
            key (str): Name of config option.
            type (type, optional): Type to cast config value to. Defaults to str.

        Returns:
            Any: Config value.
        """
        self.lock.lockForRead()
        # notably QSettings assume strings too unless specified
        assert self.config.contains(key) and hasattr(
            self.model, key
        ), "Report this bug, developer missed out a config key somewhere."
        val = self.config.value(key, type=type)
        self.lock.unlock()
        return val

    def set(self, key: str, val: Any, overwrite: bool = True):
        """Set config value by key.

        Args:
            key (str): Name of config option.
            val (Any): Config value.
            overwrite (bool, optional): Whether to overwrite an existing value. Defaults to False.
        """
        self.lock.lockForWrite()
        if overwrite or not self.config.contains(key):
            self.config.setValue(key, val)
        self.lock.unlock()

    def restore_defaults(self, overwrite: bool = True):
        """Reset settings to default.

        Args:
            overwrite (bool, optional): Whether to overwrite existing settings, else add only new ones. Defaults to True.
        """
        defaults = asdict(self.model)
        for k, v in defaults.items():
            self.set(k, v, overwrite)
