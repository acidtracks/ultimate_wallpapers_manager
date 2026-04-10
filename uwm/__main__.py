import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m uwm",
        description="Ultimate Wallpapers Manager",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Récupérer et appliquer un fond d'écran")
    p_fetch.add_argument("--title", help="Chercher directement ce titre sur Wallhaven")

    sub.add_parser("watch", help="Démarrer le watcher MPRIS + Hyprland")

    args = parser.parse_args()

    if args.cmd == "fetch":
        from uwm import fetcher
        if args.title:
            fetcher.fetch_for_title(args.title)
        else:
            fetcher.fetch_random()

    elif args.cmd == "watch":
        from uwm import watcher
        watcher.run()


if __name__ == "__main__":
    main()
