import tempfile, os, sys, json, traceback, datetime
sys.path.extend([os.path.join(os.path.dirname(os.path.realpath(__file__)), ".")])
from m_constants import *

tmp_path = os.path.join(tempfile.gettempdir(), TMP_DIR)
config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

def get_weight_path():
    weight_path = os.path.abspath(os.path.join(config_path, WEIGHTS_FOLDER))
    with open(os.path.join(config_path, CONFIG_FILE), "r") as f:
        config = json.load(f)
        try:
            weight_path = config["weight_path"]
        except:
            print("no weights path found in config, using default:", weight_path)
            #pass
    return weight_path

weight_path = get_weight_path()

def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def init_tmp():
    if not os.path.isdir(tmp_path):
        os.makedirs(tmp_path)

def cleanup_tmp():
    for root, dirs, files in os.walk(tmp_path, topdown=False):
        for name in files:
            if "input" in name or "result" in name or "cache" in name:
                os.remove(os.path.join(root, name))
    os.rmdir(tmp_path)

def get_temp_path():
    return tmp_path
    
def get_config_path():
    return config_path

def get_config():
    with open(os.path.join(config_path, CONFIG_FILE), "r") as f:
        return json.load(f)
        
def get_model_config(model_name: str = ''):
    with open(os.path.join(config_path, WEIGHTS_FOLDER, (
            model_name + '_' if model_name else '') + CONFIG_FILE), "r") as f:
        return json.load(f)
        
def set_model_config(config, model_name: str = ''):
    with open(os.path.join(config_path, WEIGHTS_FOLDER, (
            model_name + '_' if model_name else '') + CONFIG_FILE), "w") as f:
        return json.dump(config, f)
        
def handle_exceptions(module_name):
    def decorator(fn_name):
        if fn_name is None: return
        def wrapper(*args, **kwargs):
            try:
                fn_name(*args, **kwargs)
                # Remove old temporary error files that were saved
                for f_name in os.listdir(os.path.join(weight_path,"..")):
                    if ERROR_LOG in f_name: os.remove(os.path.join(weight_path,"..", f_name))
            except Exception as error:
                error_text = traceback.format_exc()
                error_text = error_text.replace(config_path, '').replace(os.getenv('APPDATA'), "%APPDATA%")
                error_text = error_text.splitlines()[3:]
                print('\n'.join(error_text))
                error_text = [((line[:200]+"...") if len(line)>200 else line) for line in error_text]
                error_text = [(line[2:] if (line[0:2] == "  ") else line) for line in error_text]
                error_text = '\n'.join(error_text)
                
                set_model_config({"inference_status": "failed", "last_error": error_text}, module_name)
        return wrapper
    return decorator
