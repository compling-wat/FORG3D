"""Download 3D model from Objaverse."""
import argparse
import os

import objaverse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-path', type=str, default='data/.objaverse',
                        help='Output directory')
    parser.add_argument('--uids', type=str, nargs='+', required=True,
                        help='Objaverse UID')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    objaverse.BASE_PATH = args.base_path
    objaverse._VERSIONED_PATH = os.path.join(objaverse.BASE_PATH, "hf-objaverse-v1")
    objects = objaverse.load_objects(uids=args.uids)
    print(objects)
