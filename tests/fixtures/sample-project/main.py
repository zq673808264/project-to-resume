import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("note")
    args = parser.parse_args()
    print(f"Summarizing {args.note}")


if __name__ == "__main__":
    main()
