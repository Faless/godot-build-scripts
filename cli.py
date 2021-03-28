#!/usr/python

import argparse
import logging
import os
import sys

from builder import GitRunner, PodmanRunner, ImageConfigs, BuildConfigs


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    containers = [cls.__name__.replace("Config", "") for cls in ImageConfigs]
    parser = argparse.ArgumentParser()
    parser.add_argument("godot_version", help="godot version (e.g. 3.1-alpha5)")

    # Registry options
    parser.add_argument("-r", "--registry")
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")

    parser.add_argument("-g", "--git", help="git treeish, possibly a git ref, or commit hash.", default="origin/master")
    parser.add_argument("-b", "--build", choices=["all", "classical", "mono"], default="all")
    parser.add_argument("-k", "--container", action="append", default=[], help="The containers to build, one of %s" % containers)
    parser.add_argument("-f", "--force-download", action="store_true")
    parser.add_argument("-s", "--skip-download", action="store_true")
    parser.add_argument("-c", "--skip-git", action="store_true")
    parser.add_argument("-t", "--skip-tar", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("--no-check", "--nc", action="store_true")
    args = parser.parse_args()
    pwd = os.path.dirname(os.path.realpath(__file__))
    git = GitRunner(pwd, dry_run=args.dry_run)
    podman = PodmanRunner(pwd, registry=args.registry, username=args.username, password=args.password, dry_run=args.dry_run)
    build_mono = args.build == "all" or args.build == "mono"
    build_classical = args.build == "all" or args.build == "classical"
    if not args.skip_download:
        podman.fetch_images(force=args.force_download)
    if not args.skip_git:
        git.checkout(args.git)
    if not args.no_check:
        git.check_version(args.godot_version)
    if not args.skip_tar:
        git.tgz(args.godot_version)
    for c in args.container:
        if not c in containers:
            print("Unknown container: %s. Must be one of: %s" % (c, containers))
            sys.exit(1)
    if len(args.container) == 0:
        args.container = containers
    to_build = [ImageConfigs[containers.index(c)] for c in args.container]
    for b in to_build:
        podman.podrun(b, classical=build_classical, mono=build_mono)
