#!/usr/python

import sys
import os

from .runner import RunError, run as _run

def run(cmd, **kwargs):
    if not 'lock' in kwargs:
        kwargs['lock'] = True
    if not 'verbose' in kwargs:
        kwargs['verbose'] = True
    return _run(cmd, **kwargs)

def which(what):
    return run(["which", what])[0].strip()


class Builder:
    IMAGES = ["mono-glue", "windows", "ubuntu-64", "ubuntu-32", "javascript"]
    IMAGES_PRIVATE = ["macosx", "android", "ios", "uwp"]

    def __init__(self, base_dir, args):
        self.base_dir = base_dir
        self.args = args
        self._podman = self._detect_podman()
        self.build_name = os.environ.get('BUILD_NAME', "custom_build")

    def _detect_podman(self):
        podman = which("podman")
        if not podman:
            podman = which("docker")
        if not podman:
            print("Either podman or docker needs to be installed")
            sys.exit(1)
        return podman

    def podman(self, args, **kwargs):
        return run([self._podman] + args, **kwargs)

    def podman_run(self, config, **kwargs):
        def env(env_vars):
            for k, v in env_vars.items():
                yield("--env")
                yield(f"{k}={v}")

        def mount(mount_points):
            for k, v in mount_points.items():
                yield("-v")
                yield(f"{self.base_dir}/{k}:/root/{v}")

        for d in config.dirs:
            self.ensure_dir(os.path.join(self.base_dir, d))

        cores = os.environ.get('NUM_CORES', os.cpu_count())
        cmd = [self._podman, "run", "--rm", "-w", "/root/"]
        cmd += env({
            "BUILD_NAME": os.environ.get("BUILD_NAME", "custom_build"),
            "NUM_CORES": os.environ.get("NUM_CORES", os.cpu_count()),
            "CLASSICAL": 0,
            "MONO": 1, # TODO
        })
        cmd += mount({
            "mono-glue": "mono-glue",
            "godot.tar.gz": "godot.tar.gz",
        })
        cmd += mount(config.mounts)
        if config.out_dir is not None:
            out_dir = f"out/{config.out_dir}"
            self.ensure_dir(out_dir)
            cmd += mount({
                out_dir: "out"
            })

        cmd += ["%s:%s" % (config.image, config.image_version)] + config.args

        if config.log and not 'log' in kwargs:
            self.ensure_dir("out/logs")
            with open(os.path.join(self.base_dir, "out", "logs", config.log), "w") as log:
                return run(cmd, log=log, **kwargs)
        else:
            return run(cmd, **kwargs)

    def git(self, *args):
        return run(["git"] + list(args))

    def fetch_image(self, registry, image, force=False):
        # TODO for real, and handle failures
        exists = not force and self.podman(["image", "exists", image])[2] == 0
        if not exists:
            #run([podman, "pull", "%s/%s" % (registry, image)])
            print(exists)

    def fetch_images(self):
        registry = self.args.registry
        force = self.args.force_download
        # TODO selective
        for image in Builder.IMAGES:
            self.fetch_image(registry, "godot/%s" % image)
        for image in Builder.IMAGES_PRIVATE:
            self.fetch_image(registry, "godot-private/%s" % image)

    def check_version(self, godot_version):
        import importlib.util
        version_file = os.path.join("git", "version.py")
        spec = importlib.util.spec_from_file_location("version", version_file)
        version = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(version)
        if hasattr(version, "patch"):
            version_string = f"{version.major}.{version.minor}.{version.patch}-{version.status}"
        else:
            version_string = f"{version.major}.{version.minor}-{version.status}"
        ok = version_string == godot_version
        if not ok:
            print(f"Version mismatch, expected: {godot_version}, got: {version_string}")
            sys.exit(1)

    def checkout(self, ref):
        repo = "https://github.com/godotengine/godot"
        dest = os.path.join(self.base_dir, "git")
        # TODO error handling, prompt for reset.
        self.git("clone", dest)
        self.git("-C", dest, "fetch", "--all")
        self.git("-C", dest, "checkout", "--detach", ref)

    def ensure_dir(self, dirname):
        os.makedirs(dirname, exist_ok=True)

    def tgz(self, version, ref="HEAD"):
        source = os.path.join(self.base_dir, "git")
        dest = os.path.join(self.base_dir, "godot.tar.gz")
        self.git("-C", source, "archive", f"--prefix=godot-{version}/", "-o", dest, ref)
