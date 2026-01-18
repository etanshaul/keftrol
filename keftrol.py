#!/usr/bin/env python3
"""KEF tray controller for input switching and volume control."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, Gdk, AyatanaAppIndicator3 as AppIndicator3

from pykefcontrol import KefConnector
import threading

SPEAKER_IP = "192.168.10.229"

INPUTS = [
    ("wifi", "Wi-Fi"),
    ("bluetooth", "Bluetooth"),
    ("tv", "TV"),
    ("optical", "Optical"),
    ("usb", "USB"),
]


class KefTray:
    def __init__(self):
        self.speaker = None
        self.window = None
        self.volume_scale = None
        self.mute_button = None
        self.input_buttons = {}
        self.updating_ui = False

        self.create_tray()
        self.create_window()
        self.connect_speaker()

    def create_tray(self):
        self.indicator = AppIndicator3.Indicator.new(
            "keftrol",
            "audio-speakers",
            AppIndicator3.IndicatorCategory.HARDWARE
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()

        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self.show_window)
        menu.append(open_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

    def show_window(self, widget=None):
        self.update_ui_from_speaker()
        self.window.show_all()
        self.window.present()

    def quit(self, widget=None):
        Gtk.main_quit()

    def connect_speaker(self):
        def do_connect():
            try:
                self.speaker = KefConnector(SPEAKER_IP)
                GLib.idle_add(self.update_ui_from_speaker)
            except Exception as e:
                print(f"Failed to connect to speaker: {e}")

        threading.Thread(target=do_connect, daemon=True).start()

    def update_ui_from_speaker(self):
        if not self.speaker or self.updating_ui:
            return

        self.updating_ui = True
        try:
            current_source = self.speaker.source
            for source_id, btn in self.input_buttons.items():
                btn.set_active(source_id == current_source)

            if self.volume_scale:
                volume = self.speaker.volume
                self.volume_scale.set_value(volume)
        except Exception as e:
            print(f"Error updating UI: {e}")
        finally:
            self.updating_ui = False

    def create_window(self):
        self.window = Gtk.Window(title="KEF Control")
        self.window.set_default_size(320, -1)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.connect("delete-event", self.on_delete)
        self.window.connect("key-press-event", self.on_key_press)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        self.window.add(vbox)

        title = Gtk.Label(label="KEF")
        title.get_style_context().add_class("title")
        vbox.pack_start(title, False, False, 0)

        input_label = Gtk.Label(label="Input")
        input_label.set_halign(Gtk.Align.START)
        input_label.get_style_context().add_class("dim-label")
        vbox.pack_start(input_label, False, False, 0)

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        input_box.set_homogeneous(True)
        vbox.pack_start(input_box, False, False, 0)

        first_btn = None
        for source_id, label in INPUTS:
            if first_btn is None:
                btn = Gtk.RadioButton(label=label)
                first_btn = btn
            else:
                btn = Gtk.RadioButton.new_with_label_from_widget(first_btn, label)
            btn.set_mode(False)
            btn.connect("toggled", self.on_input_changed, source_id)
            input_box.pack_start(btn, True, True, 0)
            self.input_buttons[source_id] = btn

        vol_label = Gtk.Label(label="Volume")
        vol_label.set_halign(Gtk.Align.START)
        vol_label.get_style_context().add_class("dim-label")
        vbox.pack_start(vol_label, False, False, 0)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vbox.pack_start(vol_box, False, False, 0)

        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.volume_scale.set_draw_value(True)
        self.volume_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        vol_box.pack_start(self.volume_scale, True, True, 0)

        self.mute_button = Gtk.ToggleButton(label="Mute")
        self.mute_button.connect("toggled", self.on_mute_toggled)
        vol_box.pack_start(self.mute_button, False, False, 0)

    def on_delete(self, widget, event):
        self.window.hide()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.window.hide()
            return True
        return False

    def on_input_changed(self, button, source_id):
        if self.updating_ui or not button.get_active():
            return

        def do_change():
            try:
                self.speaker.source = source_id
            except Exception as e:
                print(f"Error changing input: {e}")

        threading.Thread(target=do_change, daemon=True).start()

    def on_volume_changed(self, scale):
        if self.updating_ui:
            return

        volume = int(scale.get_value())

        def do_change():
            try:
                self.speaker.set_volume(volume)
            except Exception as e:
                print(f"Error changing volume: {e}")

        threading.Thread(target=do_change, daemon=True).start()

    def on_mute_toggled(self, button):
        if self.updating_ui:
            return

        def do_toggle():
            try:
                if button.get_active():
                    self.speaker.mute()
                else:
                    self.speaker.unmute()
            except Exception as e:
                print(f"Error toggling mute: {e}")

        threading.Thread(target=do_toggle, daemon=True).start()


def main():
    app = KefTray()
    Gtk.main()


if __name__ == "__main__":
    main()
