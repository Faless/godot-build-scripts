
class ImageConfig:

    def __getattr__(self, name):
        try:
            return self.__class__.getattr(name)
        except AttributeError as e:
            return super().__getattr__(name)

    out_dir = None
    dirs = ["out"]
    args = ["bash", "/root/build/build.sh"]
    mounts = {}
    image_version = "3.3-mono-6.12.0.114"
    log = None


class MonoGlueConfig(ImageConfig):
    dirs = ["mono-glue"]
    mounts = {"build-mono-glue": "build"}
    image = "localhost/godot-mono-glue"
    log = "mono-glue"


class WindowsConfig(ImageConfig):
    out_dir = "windows"
    dirs = ["out/windows"]
    mounts = {"build-windows": "build"}
    image = "localhost/godot-windows"
    log = "windows"


class JavaScriptConfig(ImageConfig):
    out_dir = "javascript"
    dirs = ["out/javascript"]
    mounts = {"build-javascript": "build"}
    image = "localhost/godot-javascript"
    log = "javascript"

configs = ImageConfig.__subclasses__()
