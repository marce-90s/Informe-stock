from pathlib import Path

import kagglehub


COMPETITION = "inventory-optimization"
OUTPUT_DIR = Path("data/raw/inventory-optimization")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    path = kagglehub.competition_download(
        COMPETITION,
        output_dir=str(OUTPUT_DIR),
    )

    print(f"Competition files downloaded to: {path}")


if __name__ == "__main__":
    main()
