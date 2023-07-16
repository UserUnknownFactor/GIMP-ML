#!/usr/bin/env python3
# coding: utf-8
"""
 .d8888b.  8888888 888b     d888 8888888b.       888b     d888 888
d88P  Y88b   888   8888b   d8888 888   Y88b      8888b   d8888 888
888    888   888   88888b.d88888 888    888      88888b.d88888 888
888          888   888Y88888P888 888   d88P      888Y88888P888 888
888  88888   888   888 Y888P 888 8888888P"       888 Y888P 888 888
888    888   888   888  Y8P  888 888             888  Y8P  888 888
Y88b  d88P   888   888   "   888 888             888   "   888 888
 "Y8888P88 8888888 888       888 888             888       888 88888888


Performs inpainting on a given image with another mask layer.
"""
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, GObject, GLib, Gio, Gtk
import gettext, subprocess, os, sys, json
sys.path.extend([os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")])
from plugin_utils import *
from module_utils import *
from constants import *

_ = gettext.gettext

model_dict = {MODEL_PLACES2: "places2", MODEL_CELEBA: "celeba", MODEL_PARISSW: "psv"}
model_name_enum = StringEnum(
    MODEL_PLACES2,
    _(MODEL_PLACES2),
    MODEL_CELEBA,
    _(MODEL_CELEBA),
    MODEL_PARISSW,
    _(MODEL_PARISSW),
)

def inpainting(
    procedure,
    image,
    n_drawables,
    masked_layer,
    mask,
    force_cpu,
    model_name,
    progress_bar,
    config_path_output,
):
    # Save inference parameters and layers
    weight_path = config_path_output["weight_path"]
    python_path = config_path_output["python_path"]
    plugin_path = config_path_output["plugin_path"]

    undo_group_start(image)
    init_tmp()

    save_image(os.path.join(tmp_path, BASE_IMG), image, masked_layer)
    save_image(os.path.join(tmp_path, MASK_IMG), image, mask)

    set_model_config({
            "force_cpu": bool(force_cpu),
            "n_drawables": n_drawables,
            "model_name": model_dict[model_name],
            "inference_status": "started",
        }, PLUGIN_ID)

    # Run inference and load as layer
    subprocess.call([python_path, plugin_path])
    data_output = get_model_config(PLUGIN_ID)

    if data_output["inference_status"] == "success":
        load_single_result_and_insert(RESULT_IMG, image, "InPaint")
        undo_group_end(image)
        cleanup_tmp() # Remove temporary images
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    else:
        undo_group_end(image)
        elog = "See GIMP console for error text"
        if "last_error" in data_output: elog = data_output["last_error"]
        show_dialog(
            "Enlightening was not performed due to errors.\nError text:\n" + elog,
            "Error!", "error", image_paths
        )
        cleanup_tmp() # Remove temporary images
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


def run(procedure, run_mode, image, n_drawables, layer, args, data):
    force_cpu = args.index(0)
    model_name = args.index(1)

    if run_mode == Gimp.RunMode.INTERACTIVE:
        # Get all paths
        config_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "..", "tools"
        )
        config_path_output = get_config()
        python_path = config_path_output["python_path"]
        config_path_output["plugin_path"] = os.path.join(config_path, PLUGIN_ID, "inpainting.py")

        config = procedure.create_config()
        config.set_property("force_cpu", force_cpu)
        config.begin_run(image, run_mode, args)

        GimpUi.init("inpainting.py")
        use_header_bar = Gtk.Settings.get_default().get_property(
            "gtk-dialogs-use-header"
        )

        # Check selected layers
        ltype = type(layer[0]).__name__
        try:
            if ltype == "LayerMask":
                mask = layer[0]
                masked_layer = get_masked_layer(mask)
            else:
                masked_layer = layer[0]
                mask = get_layer_mask(masked_layer)
        except:
            n_drawables = 0

        if n_drawables != 1 or not mask:
            show_dialog(
                "Please select an image layer containing a mask.", "Error!", "error", image_paths
            )
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        n_drawables_text = _("Mask Selected |")

        # Create UI
        dialog = GimpUi.Dialog(use_header_bar=use_header_bar, title=_("InPainting..."))
        dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("_Help"), Gtk.ResponseType.APPLY)
        dialog.add_button(_("_Inpaint"), Gtk.ResponseType.OK)

        vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, homogeneous=False, spacing=10
        )
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

        # Show Logo
        logo = Gtk.Image.new_from_file(image_paths["logo"])
        # grid.attach(logo, 0, 0, 1, 1)
        vbox.pack_start(logo, False, False, 1)
        logo.show()

        # Show License
        license_text = _(PLUGIN_LICENSE)
        label = Gtk.Label(label=license_text)
        # grid.attach(label, 1, 1, 1, 1)
        vbox.pack_start(label, False, False, 1)
        label.show()

        # Show n_drawables text
        label = Gtk.Label(label=n_drawables_text)
        grid.attach(label, 0, 0, 1, 1)
        label.show()

        # Show ideal image size text
        label = Gtk.Label(label="256 X 256 px")
        grid.attach(label, 1, 0, 1, 1)
        label.show()

        progress_bar = Gtk.ProgressBar()
        vbox.add(progress_bar)
        progress_bar.show()

        # Force CPU parameter
        spin = GimpUi.prop_check_button_new(config, "force_cpu", _("Force _CPU"))
        spin.set_tooltip_text(
            _(
                "If checked, CPU is used for model inference."
                " Otherwise, GPU will be used if available."
            )
        )
        grid.attach(spin, 2, 0, 1, 1)
        spin.show()

        # Model Name parameter
        label = Gtk.Label.new_with_mnemonic(_("_Model Name"))
        grid.attach(label, 3, 0, 1, 1)
        label.show()
        combo = GimpUi.prop_string_combo_box_new(
            config, "model_name", model_name_enum.get_tree_model(), 0, 1
        )
        grid.attach(combo, 4, 0, 1, 1)
        combo.show()

        # Wait for user to click
        dialog.show()
        while True:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                force_cpu = config.get_property("force_cpu")
                model_name = config.get_property("model_name")
                result = inpainting(
                    procedure,
                    image,
                    n_drawables,
                    masked_layer,
                    mask,
                    force_cpu,
                    model_name,
                    progress_bar,
                    config_path_output,
                )
                # If the execution was successful, save parameters so they will be restored next time we show dialog.
                if result.index(0) == Gimp.PDBStatusType.SUCCESS and config is not None:
                    config.end_run(Gimp.PDBStatusType.SUCCESS)
                return result
            elif response == Gtk.ResponseType.APPLY:
                url = HELP_URL + "item-7-1"
                Gio.app_info_launch_default_for_uri(url, None)
                continue
            else:
                dialog.destroy()
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CANCEL, GLib.Error()
                )


class InPainting(Gimp.PlugIn):
    ## Parameters ##
    __gproperties__ = {
        "force_cpu": (
            bool,
            _("Force _CPU"),
            "Force CPU",
            True,
            GObject.ParamFlags.READWRITE
        ),
        "model_name": (
            str,
            _("Model Name"),
            f"Model Name: '{MODEL_PLACES2}', '{MODEL_CELEBA}', '{MODEL_PARISSW}'",
            MODEL_PLACES2,
            GObject.ParamFlags.READWRITE
        ),
    }

    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return [PLUGIN_ID]

    def do_set_i18n(self, procname):
        return False, 'gimp30-python', None

    def do_create_procedure(self, name):
        procedure = None
        if name == PLUGIN_ID:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, run, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
            procedure.set_documentation(
                N_("Performs inpainting on a given image with GIMP mask layer."),
                globals()["__doc__"], 
                name,
            )
            procedure.set_menu_label(N_("_InPainting..."))
            procedure.set_attribution(*ATTRIBUTION_INFO)
            procedure.add_menu_path(MENU_LOCATION)
            procedure.add_argument_from_property(self, "force_cpu")
            procedure.add_argument_from_property(self, "model_name")
        return procedure


Gimp.main(InPainting.__gtype__, sys.argv)
