#from __future__ import print_function, absolute_import, division
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, GObject, GLib, Gio, Gtk
import gettext, subprocess, os, sys, json, tempfile, traceback
_ = gettext.gettext

from plugin_utils import *
from module_constants import *

#from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

base_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
models_dir = os.path.join(base_dir, "models")
config_data = get_config()

def configure_plugin(       
            label = "_Plugin..."
            help_text="Generic GIMP plugin",     
            sensitivity_mask=Gimp.ProcedureSensitivityMask.DRAWABLE,
            image_types="RGB*, GRAY*",
    ):
    def _do_create_procedure(self, name)
        procedure = None
        if name == self.PLUGIN_ID:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, run_outer, None)
            procedure.set_image_types(image_types)
            procedure.set_sensitivity_mask(sensitivity_mask)
            procedure.set_documentation(
                help_text
                "", #globals()[ "__doc__" ],  # Include docstring from filestart
                name,
            )
            procedure.set_menu_label(N_(label))
            procedure.set_attribution(*ATTRIBUTION_INFO)
            procedure.add_menu_path(MENU_LOCATION)
            procedure.add_argument_from_property(self, "force_cpu")
        return procedure
    return _do_create_procedure
    
def default_run(
    main_procedure,
    label="Plugin...",
    main_button="Run Inference",
    help_text = "",
    plugin_license = "PLUGIN LICENSE:  MIT"
    model_file = None,
    ):
    def _run(self, args):
        force_cpu = args.index(0)
        if run_mode == Gimp.RunMode.INTERACTIVE:   
            config = procedure.create_config()
            config.set_property("force_cpu", force_cpu)
            config.begin_run(image, run_mode, args)
    
            GimpUi.init(os.path.filename(__file__))
            use_header_bar = Gtk.Settings.get_default().get_property( "gtk-dialogs-use-header")
            dialog = GimpUi.Dialog(use_header_bar=use_header_bar, title=_(title))
            dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
            dialog.add_button(_("_Help"), Gtk.ResponseType.APPLY)
            dialog.add_button(_(f"{PLUGIN_MAIN_BTN}"), Gtk.ResponseType.OK)
    
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10)
            dialog.get_content_area().add(vbox)
            vbox.show()
    
            # Create grid to set all the properties inside.
            grid = Gtk.Grid()
            grid.set_column_homogeneous(False)
            grid.set_border_width(10)
            grid.set_column_spacing(10)
            grid.set_row_spacing(10)
            vbox.add(grid)
            grid.show()
    
            # Force CPU parameter
            spin = GimpUi.prop_check_button_new(config, "force_cpu", _("Force _CPU"))
            spin.set_tooltip_text(
                _(
                    "If checked, CPU is used for model inference."
                    " Otherwise, GPU will be used if available."
                )
            )
            grid.attach(spin, 1, 2, 1, 1)
            spin.show()
    
            # Show Logo
            logo = Gtk.Image.new_from_file(image_paths["logo"])
            vbox.pack_start(logo, False, False, 1)
            logo.show()
    
            # Show License
            label = Gtk.Label(label=_(plugin_license))
            vbox.pack_start(label, False, False, 1)
            label.show()
    
            progress_bar = Gtk.ProgressBar()
            vbox.add(progress_bar)
            progress_bar.show()
    
            # Wait for user to click
            dialog.show()
            while True:
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    force_cpu = config.get_property("force_cpu")
                    self._last_result = self.predict(self.drawables[0])
                    # If the execution was successful, save parameters so they will be restored next time we show dialog.
                    if result.index(0) == Gimp.PDBStatusType.SUCCESS and config is not None:
                        config.end_run(Gimp.PDBStatusType.SUCCESS)
                    return result
                elif response == Gtk.ResponseType.APPLY:
                    url = HELP_URL + help_text
                    Gio.app_info_launch_default_for_uri(url, None)
                    continue
                else:
                    dialog.destroy()
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

class GimpPluginBase(Gimp.PlugIn):
    # Parameters #
    __gproperties__ = {
        "force_cpu": (
            bool, _("Force _CPU"), "Force CPU", True, GObject.ParamFlags.READWRITE,
        ),
    }

    # GimpPlugIn virtual methods #
    def do_query_procedures(self):
        return [self.PLUGIN_ID]

    def do_set_i18n(self, procname):
        return False, 'gimp30-python', None

    def __init__(self):
        self.predictor_file = None
        self.gimp_img = None
        self.drawable = None
        self.name = None
        self.PLUGIN_ID = os.path.basename(__file__).replace(".py", '')
        
    def init_tmp(self.tmp_path):
        if not os.path.isdir(self.tmp_path):
            os.makedirs(self.tmp_path)
    
    def cleanup_tmp():
        for root, dirs, files in os.walk(self.tmp_path, topdown=False):
            for name in files:
                if "input" in name or "result" in name or "cache" in name:
                    os.remove(os.path.join(root, name))
        os.rmdir(self.tmp_path)

    def run_outer(self, procedure, run_mode, gimp_img, n_drawables, layers, extra_args, data):
        self.gimp_img = gimp_img
        self.drawables = layers
        self.n_drawables = n_drawables
        
        print(f"Running {self.name}...")
        undo_group_start(gimp_img)
        #init_progress(f"Running {self.name}...")
        self.run(extra_args)
        undo_group_end(self.gimp_img)
        #end_progress()

    def predict(self, *args, **kwargs):
        assert self.predictor_file is not None

        # Save inference parameters and layers
        weight_path = config_path_output["weight_path"]
        python_path = config_path_output["python_path"]
        plugin_path = config_path_output["plugin_path"]
    
        undo_group_start(image)
        init_tmp()
    
        save_image(BASE_IMG, image, drawables[0])
    
        set_model_config({
                "force_cpu": bool(force_cpu),
                "inference_status": "started",
            }, PLUGIN_ID)
    
        # Run inference and load as layer
        subprocess.call([python_path, plugin_path])
        data_output = get_model_config(PLUGIN_ID)
    
        if data_output["inference_status"] == "success":
            load_single_result_and_insert(RESULT_IMG, image, f"{PLUGIN_LAYER_NAME}")
            undo_group_end(image)
            cleanup_tmp() # Remove temporary images
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
        else:
            undo_group_end(image)
            elog = "See GIMP console for error text"
            if "last_error" in data_output: elog = data_output["last_error"]
            show_dialog(
                f"{PLUGIN_VERB} was not performed due to errors.\nError text:\n" + elog,
                "Error!", "error", image_paths
            )
            cleanup_tmp() # Remove temporary images
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
        
'''
        proxy = InferenceProxy(self.predictor_file)
        try:
            return proxy(*args, **kwargs)
        except Exception as e:
            show_dialog(
                ERROR_TEXT + "\n" + self._format_error(traceback.format_exc())
                "Error!", "error",
                image_paths
            )


class InferenceProxy(object):
    """
    When called, runs:
        python3 models/<predictor_file>
    and waits for the subprocess to call get_args() and then return_result()
    or raise_error() over XML-RPC.
    Additionally, progress info can be reported via update_progress().
    """

    def __init__(self, predictor_file):
        self.python_executable = config_data["python_path"]
        self.model_path = os.path.join(models_dir, predictor_file)
        self.server = None
        self.args = None
        self.kwargs = None
        self.result = None

    @staticmethod
    def _encode(x):
        if isinstance(x, gimp.Layer):
            x = layer_to_imgarray(x)
        if isinstance(x, ImgArray):
            x = x.encode()
        return x

    @staticmethod
    def _decode(x):
        if isinstance(x, list) and len(x) == 3 and x[0] == 'ImgArray':
            x = ImgArray.decode(x)
        return x

    def _rpc_get_args(self):
        assert isinstance(self.args, (list, tuple))
        assert isinstance(self.kwargs, dict)
        args = [self._encode(arg) for arg in self.args]
        kwargs = {k: self._encode(v) for k, v in self.kwargs.items()}
        return args, kwargs

    def _rpc_return_result(self, result):
        assert isinstance(result, (list, tuple))
        self.result = tuple(self._decode(x) for x in result)
        threading.Thread(target=lambda: self.server.shutdown()).start()

    def _rpc_raise_exception(self, exc_string):
        self.server.exception = exc_string
        threading.Thread(target=lambda: self.server.shutdown()).start()

    def _start_subprocess(self, rpc_port):
        try:
            self.proc = subprocess.Popen([
                self.python_executable,
                self.model_path,
                'http://127.0.0.1:{}/'.format(rpc_port)
            ], env=env)
            self.proc.wait()
        finally:
            self.server.shutdown()
            self.server.server_close()

    def _init_rpc_server(self):
        # For cleaner exception info
        class RequestHandler(SimpleXMLRPCRequestHandler):
            def _dispatch(self, method, params):
                try:
                    return self.server.funcs[method](*params)
                except:
                    self.server.exception = sys.exc_info()
                    raise

        self.server = SimpleXMLRPCServer(('127.0.0.1', 0), allow_none=True, logRequests=False,
                                         requestHandler=RequestHandler)
        self.server.register_function(self._rpc_get_args, 'get_args')
        self.server.register_function(self._rpc_return_result, 'return_result')
        self.server.register_function(self._rpc_raise_exception, 'raise_exception')
        self.server.register_function(update_progress)
        self.server.exception = None
        rpc_port = self.server.server_address[1]
        return rpc_port

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        rpc_port = self._init_rpc_server()
        t = threading.Thread(target=self._start_subprocess, args=(rpc_port,))
        t.start()
        self.server.serve_forever()

        if self.result is None:
            if self.server.exception:
                if isinstance(self.server.exception, str):
                    raise RuntimeError(self.server.exception)
                type, value, traceback = self.server.exception
                raise type, value, traceback
            raise RuntimeError(_("Model did not return a result!"))

        if len(self.result) == 1:
            return self.result[0]
        return self.result


class ImgArray(object):
    """Minimal Numpy ndarray-like object for serialization in RPC."""

    def __init__(self, buf, shape):
        self._buffer = buf
        self._shape = shape

    def encode(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(self.buffer)
            temp_path = f.name
        return "ImgArray", temp_path, self._shape

    @staticmethod
    def decode(x):
        temp_path, shape = x[1:]
        with open(temp_path, mode='rb') as f:
            data = f.read()
        os.unlink(temp_path)
        return ImgArray(data, shape)
'''
