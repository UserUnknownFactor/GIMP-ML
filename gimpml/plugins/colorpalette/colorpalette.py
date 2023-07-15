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

Opens the color palette as a new scaled layer in GIMP.
"""
import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp, GLib, Gio
import sys, os
sys.path.extend([os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")])
from plugin_utils import load_image_as_layer, N_, ATTRIBUTION_INFO


def colorpalette(procedure, run_mode, image, n_drawables, drawable, args, data):
    gimp_layer = load_image_as_layer(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "color_palette.png"
        ), 
        image
    )
    if (gimp_layer.index(0) == Gimp.PDBStatusType.SUCCESS):
        gimp_layer = gimp_layer.index(1)
        gimp_layer.set_name("Color Palette")
        gimp_layer.set_mode(Gimp.LayerMode.NORMAL)
        image.insert_layer(gimp_layer, None, -1)
        Gimp.get_pdb().run_procedure('gimp-layer-resize', [gimp_layer, 1200, 675, 0, 0])
        gimp_layer = Gimp.get_pdb().run_procedure(
            'gimp-item-transform-scale', 
            [ gimp_layer, 0.0, 0.0, float(image.get_width()), float(image.get_height())]
        )

    Gimp.displays_flush()
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

class ColorPalette(Gimp.PlugIn):
    __gproperties__ = {}

    def do_query_procedures(self):
        return ["colorpalette"]
        
    def do_set_i18n(self, procname):
        return False, 'gimp30-python', None

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, colorpalette, None
        )
        procedure.set_image_types("*")
        procedure.set_documentation(
            N_("Opens the color palette as a new scaled layer in GIMP."), 
            globals()["__doc__"], 
            name
        )
        procedure.set_menu_label(N_("_Color Palette..."))
        procedure.set_attribution(*ATTRIBUTION_INFO)
        procedure.add_menu_path("<Image>/Tools/GIMP-ML/")
        return procedure

Gimp.main(ColorPalette.__gtype__, sys.argv)
