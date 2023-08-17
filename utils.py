import glob
import os
from fawkes import Fawkes


async def run_fawkes(input_dir_path: str, mode="min"):
    """Run fawkes on given directory

    Args:
        input_image_path (str): directory to run fawkes on
        mode (str, optional): fawkes mode. Defaults to "low".
    """
    image_paths = glob.glob(os.path.join(input_dir_path, "*"))
    image_paths = [
        path for path in image_paths if "_cloaked" not in path.split("/")[-1]
    ]

    # If you want to run fawkes on multiple images simultaneously,
    # edit batch_size argument
    # Be careful, fawkes developers advise against this
    # unless you have a very powerful computer
    protector = Fawkes(
        feature_extractor="arcface_extractor_0", gpu="0", batch_size=4, mode=mode
    )

    protector.run_protection(image_paths=image_paths, sd=1e7)
