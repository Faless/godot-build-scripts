from argparse import ArgumentParser

from . import ImageConfigs, GitRunner, PodmanRunner

class BaseCLI:

    def make_parser(self, base, *args, **kwargs):
        self.parser = base.add_parser(*args, **kwargs)
        self.parser.add_argument("-n", "--dry-run", action="store_true")
        self.parser.set_defaults(action_func=self.__class__.execute)


class ImageCLI(BaseCLI):

    @staticmethod
    def execute(base_dir, args):
        podman = PodmanRunner(
            base_dir,
            dry_run=args.dry_run
        )
        podman.fetch_images(
            registry=args.registry,
            username=args.username,
            password=args.password,
            force=args.force_download
        )

    def __init__(self, base):
        self.make_parser(base, "fetch", help="Fetch remote build containers")
        self.parser.add_argument("-r", "--registry")
        self.parser.add_argument("-u", "--username")
        self.parser.add_argument("-p", "--password")
        self.parser.add_argument("-f", "--force-download", action="store_true")


class GitCLI(BaseCLI):

    @staticmethod
    def execute(base_dir, args):
        git = GitRunner(base_dir, dry_run=args.dry_run)
        if not args.skip_checkout:
            git.checkout(args.treeish)
        if not args.skip_tar:
            git.tgz(args.godot_version)
        if not args.skip_check:
            git.check_version(args.godot_version)

    def __init__(self, base):
        self.make_parser(base, "checkout", help="git checkout, reset, version check, tar")
        self.parser.add_argument("godot_version", help="godot version (e.g. 3.1-alpha5)")
        self.parser.add_argument("-g", "--treeish", help="git treeish, possibly a git ref, or commit hash.", default="origin/master")
        self.parser.add_argument("-c", "--skip-checkout", action="store_true")
        self.parser.add_argument("-t", "--skip-tar", action="store_true")
        self.parser.add_argument("--skip-check", action="store_true")


class RunCLI(BaseCLI):

    @staticmethod
    def execute(base_dir, args):
        containers = [cls.__name__.replace("Config", "") for cls in ImageConfigs]
        podman = PodmanRunner(base_dir, dry_run=args.dry_run)
        build_mono = args.build == "all" or args.build == "mono"
        build_classical = args.build == "all" or args.build == "classical"
        if len(args.container) == 0:
            args.container = containers
        to_build = [ImageConfigs[containers.index(c)] for c in args.container]
        for b in to_build:
            podman.podrun(b, classical=build_classical, mono=build_mono)

    def __init__(self, base):
        containers = [cls.__name__.replace("Config", "") for cls in ImageConfigs]
        self.make_parser(base, "run", help="Run the desired containers")
        self.parser.add_argument("-b", "--build", choices=["all", "classical", "mono"], default="all")
        self.parser.add_argument("-k", "--container", action="append", default=[], help="The containers to build, one of %s" % containers)


class ReleaseCLI(BaseCLI):

    @staticmethod
    def execute(base_dir, args):
        git = GitRunner(base_dir, dry_run=args.dry_run)
        podman = PodmanRunner(base_dir, dry_run=args.dry_run)
        build_mono = args.build == "all" or args.build == "mono"
        build_classical = args.build == "all" or args.build == "classical"
        if not args.skip_download:
            podman.fetch_images(
                registry=args.registry,
                username=args.username,
                password=args.password,
                force=args.force_download
            )
        if not args.skip_git:
            git.checkout(args.git)
            git.check_version(args.godot_version)
            git.tgz(args.godot_version)

        for b in ImageConfigs:
            podman.podrun(b, classical=build_classical, mono=build_mono)

    def __init__(self, base):
        self.make_parser(base, "release", help="Make a full release cycle, git checkout, reset, version check, tar, build all")
        self.parser.add_argument("godot_version", help="godot version (e.g. 3.1-alpha5)")
        self.parser.add_argument("-r", "--registry")
        self.parser.add_argument("-u", "--username")
        self.parser.add_argument("-p", "--password")
        self.parser.add_argument("-b", "--build", choices=["all", "classical", "mono"], default="all")
        self.parser.add_argument("-s", "--skip-download", action="store_true")
        self.parser.add_argument("-c", "--skip-git", action="store_true")
        self.parser.add_argument("-g", "--git", help="git treeish, possibly a git ref, or commit hash.", default="origin/master")
        self.parser.add_argument("-f", "--force-download", action="store_true")


class CLI:

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.parser = ArgumentParser()
        subparsers = self.parser.add_subparsers(dest="action", help="The requested action", required=True)
        self.clis = [
            ImageCLI(subparsers),
            GitCLI(subparsers),
            RunCLI(subparsers),
            ReleaseCLI(subparsers),
        ]

    def execute(self):
        args = self.parser.parse_args()
        args.action_func(self.base_dir, args)
