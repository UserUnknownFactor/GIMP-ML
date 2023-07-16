import gi
gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, GObject, GLib, Gio, Gtk
import os, gettext
from module_utils import tmp_path

_ = gettext.gettext

def N_(message):
    return message

HELP_URL = "https://kritiksoman.github.io/GIMP-ML-Docs/docs-page.html#"
ATTRIBUTION_INFO = ("Kritik Soman", "GIMP-ML", "2022")
MENU_LOCATION = "<Image>/Layer/GIMP-ML/"

image_paths = {
    "colorpalette": os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "colorpalette",
        "color_palette.png",
    ),
    "logo": os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "images", "plugin_logo.png"
    ),
    "error": os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "images", "error_icon.png"
    ),
}

class StringEnum:
    """
    Helper class for when you want to use strings as keys of an enum. The values would be
    user facing strings that might undergo translation.

    The constructor accepts an even amount of arguments. Each pair of arguments
    is a key/value pair.
    """

    def __init__(self, *args):
        self.keys = []
        self.values = []

        for i in range(len(args) // 2):
            self.keys.append(args[i * 2])
            self.values.append(args[i * 2 + 1])

    def get_tree_model(self):
        """Get a tree model that can be used in GTK widgets."""
        tree_model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)
        for i in range(len(self.keys)):
            tree_model.append([self.keys[i], self.values[i]])
        return tree_model

    def __getattr__(self, name):
        """Implements access to the key. For example, if you provided a key "red", then you could access it by
        referring to
           my_enum.red
        It may seem silly as "my_enum.red" is longer to write then just "red",
        but this provides verification that the key is indeed inside enum."""
        key = name.replace("_", " ")
        if key in self.keys:
            return key
        raise AttributeError("No such key string " + key)

def undo_group_start(image):
    Gimp.context_push()
    image.undo_group_start()

def undo_group_end(image):
    image.undo_group_end()
    Gimp.context_pop()


def show_dialog(message, title, icon="logo", image_paths=None):
    use_header_bar = Gtk.Settings.get_default().get_property("gtk-dialogs-use-header")
    dialog = GimpUi.Dialog(use_header_bar=use_header_bar, title=_(title))
    # Add buttons
    #dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
    dialog.add_button(_("_OK"), Gtk.ResponseType.APPLY)
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

    # Show Logo
    logo = Gtk.Image.new_from_file(image_paths[icon])
    # vbox.pack_start(logo, False, False, 1)
    grid.attach(logo, 0, 0, 1, 1)
    logo.show()

    # Show message
    label = Gtk.Label(label=message)
    # vbox.pack_start(label, False, False, 1)
    grid.attach(label, 1, 0, 1, 1)
    label.show()
    dialog.show()
    dialog.run()
    return

def load_image_as_layer(filename, image):
    if not os.path.isfile(filename):
        return None
    return Gimp.get_pdb().run_procedure('gimp-file-load-layer', [
                GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                GObject.Value(Gimp.Image, image),
                GObject.Value(Gio.File, Gio.File.new_for_path(filename)),
            ])

def get_active_layer(image):
     layers = Gimp.get_pdb().run_procedure('gimp-image-get-selected-layers', [image])
     if layers.length() > 2:
        return layers.index(2).data
     else:
        layers = Gimp.get_pdb().run_procedure('gimp-image-get-layers', [image])
        return layers.index(2).data
        
def get_layer_mask(layer):
    return Gimp.get_pdb().run_procedure('gimp-layer-get-mask', [layer]).index(1)
    
def get_masked_layer(mask):
    return Gimp.get_pdb().run_procedure('gimp-layer-from-mask', [mask]).index(1)

def load_image_file(*argv):
    return Gimp.file_load(
            Gimp.RunMode.NONINTERACTIVE,
            Gio.file_new_for_path(os.path.join(*argv))
        )

def load_group_result_and_insert(folder, mask, image, title):
    i = 1
    group = Gimp.get_pdb().run_procedure('gimp-layer-group-new', [image])
    if (group.index(0) == Gimp.PDBStatusType.SUCCESS):
        group = group.index(1)
        group.set_name(title)
    image.insert_layer(group, None, 0)
    for fn in os.listdir(folder):
        if mask not in fn.lower(): continue
        layer = load_image_as_layer(os.path.join(folder, fn), image)
        if (layer.index(0) == Gimp.PDBStatusType.SUCCESS):
            layer = layer.index(1)
            layer.set_name(f"{title} {i:02d}")
            layer.set_mode(Gimp.LayerMode.NORMAL)
            image.insert_layer(layer, group, 0)
        i += 1
            
def load_single_result_and_insert(filename, image, title):
        fn = os.path.join(tmp_path, filename)
        if not os.path.isfile(fn):
            return
        gimp_layer = load_image_as_layer(fn, image)
        if (gimp_layer.index(0) == Gimp.PDBStatusType.SUCCESS):
            gimp_layer = gimp_layer.index(1)
            gimp_layer.set_name(title)
            gimp_layer.set_mode(Gimp.LayerMode.NORMAL)
            image.insert_layer(gimp_layer, None, 0)

def save_image(file_path, image, drawable, transparent=False):
    if drawable is None: return False
    interlace, compression = 0, 2
    config = [
            GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
            GObject.Value(Gimp.Image, image),
            GObject.Value(GObject.TYPE_INT, 1),
            GObject.Value(
                Gimp.ObjectArray, Gimp.ObjectArray.new(Gimp.Drawable, [drawable], 0)
            ),
            GObject.Value(
                Gio.File,
                Gio.File.new_for_path(os.path.join(tmp_path, file_path)),
            ),
            GObject.Value(GObject.TYPE_BOOLEAN, interlace),
            GObject.Value(GObject.TYPE_INT, compression),

            GObject.Value(GObject.TYPE_BOOLEAN, True),
            GObject.Value(GObject.TYPE_BOOLEAN, True),
            GObject.Value(GObject.TYPE_BOOLEAN, False),
            GObject.Value(GObject.TYPE_BOOLEAN, True),
    ]
    if transparent:
        config.append(GObject.Value(GObject.TYPE_BOOLEAN, True))
    Gimp.get_pdb().run_procedure("file-png-save", config)
    return True

    
def init_progress(message, gdisplay=None):
    pdb.run_procedure('gimp-progress-init', [message, gdisplay])


def end_progress():
    pdb.run_procedure('gimp-progress-end', [])


def update_progress(percentage, message):
    if percent is not None:
        pdb.run_procedure('gimp-progress-update', [percentage])
    else:
        pdb.run_procedure('gimp-progress-pulse', [])
    pdb.run_procedure('gimp-progress-set-text', [message])

