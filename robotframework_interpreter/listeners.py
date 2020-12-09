from .utils import lunr_builder
from .constants import CONTEXT_LIBRARIES

from robot.errors import DataError
from robot.libdocpkg import LibraryDocumentation
from robot.libraries.BuiltIn import BuiltIn


class RobotKeywordsIndexerListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self):
        self.builder = lunr_builder("dottedname", ["dottedname", "name"])
        self.index = None
        self.libraries = []
        self.keywords = {}

        self.library_import("BuiltIn", {})
        for name, keywords in CONTEXT_LIBRARIES.items():
            self._library_import(keywords, name)

    def library_import(self, alias, attributes):
        name = attributes.get("originalName") or alias

        if alias not in self.libraries:
            self.libraries.append(alias)
            try:
                lib_doc = LibraryDocumentation(name)
                self._library_import(lib_doc, alias)
            except DataError:
                pass

    def _library_import(self, lib_doc, alias):
        if isinstance(lib_doc, list):
            keywords = lib_doc
            doc_format = "REST"
        else:
            keywords = lib_doc.keywords
            doc_format = lib_doc.doc_format
        for keyword in keywords:
            keyword.doc_format = doc_format
            self.builder.add(
                {"name": keyword.name, "dottedname": f"{alias}.{keyword.name}"}
            )
            self.keywords[f"{alias}.{keyword.name}"] = keyword
        if len(self.keywords):
            self.index = self.builder.build()

    def resource_import(self, name, attributes):
        if name not in self.libraries:
            self.libraries.append(name)
            try:
                resource_doc = LibraryDocumentation(name)
                self._resource_import(resource_doc.keywords)
            except DataError:
                pass

    def _resource_import(self, keywords):
        for keyword in keywords:
            keyword.doc_format = "REST"
            self.builder.add(
                {"name": keyword.name, "dottedname": keyword.name}
            )
            self.keywords[keyword.name] = keyword
        if len(self.keywords):
            self.index = self.builder.build()

    def import_from_suite_data(self, suite):
        self._resource_import(suite.resource.keywords)
        try:
            for import_data in suite.resource.imports:
                attributes = {}
                if import_data.type == "Library":
                    alias = import_data.alias or import_data.name
                    attributes["originalName"] = import_data.name
                    self.library_import(alias, attributes)
                else:
                    name = import_data.name
                    self.resource_import(name, attributes)
        except AttributeError:
            pass


def clear_drivers(drivers, type_):
    remained = []
    for driver in drivers:
        if driver.get("type") != type_:
            remained.append(driver)
    drivers.clear()
    drivers.extend(remained)


def get_webdrivers(cache, type_):
    drivers = []
    for idx in range(len(cache._connections)):
        conn = cache._connections[idx]
        if conn in cache._closed:
            continue
        aliases = []
        for alias, idx_ in cache._aliases.items():
            if (idx + 1) == idx_:
                aliases.append(alias)
        drivers.append(
            dict(
                instance=conn,
                aliases=aliases,
                current=conn == cache.current,
                type=type_,
            )
        )
    return drivers


def set_webdrivers(drivers, cache, type_):
    idx = 1
    for driver in drivers:
        if driver["type"] != type_:
            continue
        cache._connections.append(driver["instance"])
        for alias in driver["aliases"]:
            cache._aliases[alias] = idx
        if driver["current"]:
            cache.current = driver["instance"]
        idx += 1


class SeleniumConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            try:
                instance = builtin.get_library_instance("SeleniumLibrary")
            except RuntimeError:
                instance = builtin.get_library_instance("Selenium2Library")
            clear_drivers(self.drivers, "selenium")
            self.drivers.extend(get_webdrivers(instance._drivers, "selenium"))
        except RuntimeError:
            pass

    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            try:
                instance = builtin.get_library_instance("SeleniumLibrary")
            except RuntimeError:
                instance = builtin.get_library_instance("Selenium2Library")
            set_webdrivers(self.drivers, instance._drivers, "selenium")
        except RuntimeError:
            pass


class RpaBrowserConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    def end_suite(self, name, attributes):
        try:
            instance = BuiltIn().get_library_instance("RPA.Browser")
            clear_drivers(self.drivers, "RPA.Browser")
            self.drivers.extend(get_webdrivers(instance._drivers, "RPA.Browser"))
        except RuntimeError:
            pass

    def start_suite(self, name, attributes):
        try:
            instance = BuiltIn().get_library_instance("RPA.Browser")
            set_webdrivers(self.drivers, instance._drivers, "RPA.Browser")
        except RuntimeError:
            pass


class JupyterConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("JupyterLibrary")
            clear_drivers(self.drivers, "jupyter")
            self.drivers.extend(get_webdrivers(instance._drivers, "jupyter"))
        except RuntimeError:
            pass

    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("JupyterLibrary")
            set_webdrivers(self.drivers, instance._drivers, "jupyter")
        except RuntimeError:
            pass


class AppiumConnectionsListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("AppiumLibrary")
            clear_drivers(self.drivers, "appium")
            self.drivers.extend(get_webdrivers(instance._cache, "appium"))
        except RuntimeError:
            pass

    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("AppiumLibrary")
            set_webdrivers(self.drivers, instance._cache, "appium")
        except RuntimeError:
            pass


class WhiteLibraryListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, drivers: list):
        self.drivers = drivers

    def end_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("WhiteLibrary")
            clear_drivers(self.drivers, "white")
            self.drivers.append(
                dict(
                    instance=(
                        getattr(instance, "app", None),
                        getattr(instance, "window", None),
                        getattr(instance, "screenshotter", None),
                    ),
                    aliases=[],
                    current=True,
                    type="white",
                )
            )
        except RuntimeError:
            pass

    def start_suite(self, name, attributes):
        try:
            builtin = BuiltIn()
            instance = builtin.get_library_instance("WhiteLibrary")
            for driver in self.drivers:
                if driver.get("type") == "white" and driver.get("current"):
                    setattr(instance, "app", driver["instance"][0])
                    setattr(instance, "window", driver["instance"][1])
                    setattr(instance, "screenshotter", driver["instance"][2])
        except RuntimeError:
            pass
