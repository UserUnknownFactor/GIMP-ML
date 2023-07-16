import hashlib, os, sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Type

try:
    import gdown
except:
    pass
import onnxruntime as ort

plugin_loc = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".")
sys.path.extend([plugin_loc])

from session_base import BaseSession
from session_cloth import ClothSession
from session_simple import SimpleSession

from gimpml.plugins.module_utils import *


def new_session(model_name: str) -> BaseSession:
    session_class: Type[BaseSession]

    if model_name == "u2netp":
        md5 = "8e83ca70e441ab06c318d82300c84806"
        url = "https://drive.google.com/uc?id=1tNuFmLv0TSNDjYIkjEdeH1IWKQdUA4HR"
        session_class = SimpleSession
    elif model_name == "u2net":
        md5 = "60024c5c889badc19c04ad937298a77b"
        url = "https://drive.google.com/uc?id=1tCU5MM1LhRgGou5OpmpjBQbSrYIUoYab"
        session_class = SimpleSession
    elif model_name == "u2net_human_seg":
        md5 = "c09ddc2e0104f800e3e1bb4652583d1f"
        url = "https://drive.google.com/uc?id=1ZfqwVxu-1XWC1xU1GHIP-FM_Knd_AX5j"
        session_class = SimpleSession
    elif model_name == "u2net_cloth_seg":
        md5 = "2434d1f3cb744e0e49386c906e5a08bb"
        url = "https://drive.google.com/uc?id=15rKbQSXQzrKCQurUjZFg8HqzZad8bcyz"
        session_class = ClothSession
    else:
        assert AssertionError(
            "Choose between u2net, u2netp, u2net_human_seg or u2net_cloth_seg"
        )

    home = os.path.join(weight_path, "u2net")
    path = os.path.join(home, f"{model_name}.onnx")
    #path.parents[0].mkdir(parents=True, exist_ok=True)

    if 'gdown' in vars() or 'gdown' in globals():
        if not os.path.exists(path):
            with redirect_stdout(sys.stderr):
                gdown.download(url, str(path), use_cookies=False)
        else:
            hashing = hashlib.new("md5", Path(path).read_bytes(), usedforsecurity=False)
            if hashing.hexdigest() != md5:
                with redirect_stdout(sys.stderr):
                    gdown.download(url, str(path), use_cookies=False)
    else:
        if not os.path.exists(path):
            print(f"Model {model_name} weights are not downloaded, please get them from {url}")

    sess_opts = ort.SessionOptions()

    if "OMP_NUM_THREADS" in os.environ:
        sess_opts.inter_op_num_threads = int(os.environ["OMP_NUM_THREADS"])

    return session_class(
        model_name,
        ort.InferenceSession(
            str(path), providers=ort.get_available_providers(), sess_options=sess_opts
        ),
    )
