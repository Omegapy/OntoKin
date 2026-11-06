"""Check the native verifier's image decoder before running the C093 tests."""
import sys


def main() -> int:
    try:
        from PIL import Image
    except (ImportError, OSError) as error:
        print(f"Native-reader setup failed: cannot import PIL.Image ({error}).", file=sys.stderr)
    else:
        if Image.__version__ == "13.0.0":
            print("Native-reader image decoder ready: Pillow 13.0.0 (PIL.Image).")
            return 0
        print(f"Native-reader setup failed: Pillow {Image.__version__} installed, expected 13.0.0.",
              file=sys.stderr)
    print("Prepare the verification environment using section 3 of OK-ENG-006.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
