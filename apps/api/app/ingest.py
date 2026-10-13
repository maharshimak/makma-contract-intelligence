import argparse
import json
from dataclasses import asdict

from app.database import SessionLocal
from app.procurement import ingest_boamp


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest public procurement source records")
    parser.add_argument("--source", choices=["BOAMP"], default="BOAMP")
    parser.add_argument("--limit", type=int, choices=range(1, 101), default=25, metavar="1..100")
    args = parser.parse_args()
    with SessionLocal() as db:
        result = ingest_boamp(db, args.limit)
    print(json.dumps(asdict(result), sort_keys=True))


if __name__ == "__main__":
    main()
