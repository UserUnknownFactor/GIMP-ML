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


Dehazes (defogs) the current layer.
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


def dehaze(procedure, image, drawables, force_cpu, progress_bar, config_path_output):
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
        load_single_result_and_insert(RESULT_IMG, image, "Dehazed")
        undo_group_end(image)
        cleanup_tmp() # Remove temporary images
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    else:
        undo_group_end(image)
        elog = "See GIMP console for error text"
        if "last_error" in data_output: elog = data_output["last_error"]
        show_dialog(
            "Inpainting was not performed due to errors.\nError text:\n" + elog,
            "Error!", "error", image_paths
        )
        cleanup_tmp() # Remove temporary images
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


def run(procedure, run_mode, image, n_drawables, layer, args, data):
    force_cpu = args.index(0)

    if run_mode == Gimp.RunMode.INTERACTIVE:
        # Get all paths
        config_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "..", "tools"
        )
        config_path_output = get_config()
        python_path = config_path_output["python_path"]
        config_path_output["plugin_path"] = os.path.join(config_path, PLUGIN_ID, "dehaze.py")

        config = procedure.create_config()
        config.set_property("force_cpu", force_cpu)
        config.begin_run(image, run_mode, args)

        GimpUi.init("dehaze.py")
        use_header_bar = Gtk.Settings.get_default().get_property(
            "gtk-dialogs-use-header"
        )
        dialog = GimpUi.Dialog(use_header_bar=use_header_bar, title=_("Dehaze..."))
        dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("_Help"), Gtk.ResponseType.APPLY)
        dialog.add_button(_("_Dehaze"), Gtk.ResponseType.OK)

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
        # grid.attach(logo, 0, 0, 1, 1)
        vbox.pack_start(logo, False, False, 1)
        logo.show()

        # Show License
        license_text = _(PLUGIN_LICENSE)
        label = Gtk.Label(label=license_text)
        # grid.attach(label, 1, 1, 1, 1)
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
                result = dehaze(
                    procedure, image, layer, force_cpu, progress_bar, config_path_output
                )
                # If the execution was successful, save parameters so they will be restored next time we show dialog.
                if result.index(0) == Gimp.PDBStatusType.SUCCESS and config is not None:
                    config.end_run(Gimp.PDBStatusType.SUCCESS)
                return result
            elif response == Gtk.ResponseType.APPLY:
                url = HELP_URL + "item-7-4"
                Gio.app_info_launch_default_for_uri(url, None)
                continue
            else:
                dialog.destroy()
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CANCEL, GLib.Error()
                )


class Dehaze(Gimp.PlugIn):
    ## Parameters ##
    __gproperties__ = {
        "force_cpu": (
            bool,
            _("Force _CPU"),
            "Force CPU",
            True,
            GObject.ParamFlags.READWRITE,
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
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE
            )
            procedure.set_documentation(
                N_("Dehazes the current layer."),
                globals()["__doc__"],  # Include docstring from the file start
                name,
            )
            procedure.set_menu_label(N_("_Dehaze..."))
            procedure.set_attribution(*ATTRIBUTION_INFO)
            procedure.add_menu_path(MENU_LOCATION)
            procedure.add_argument_from_property(self, "force_cpu")

        return procedure


Gimp.main(Dehaze.__gtype__, sys.argv)
