# gamap - systray application to change gamma
# Copyright (C) 2018 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from typing import List

import logging
import sys
import argparse
import signal
import subprocess

import Xlib.display
import Xlib.ext

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu

logger = logging.getLogger(__name__)


def get_outputs() -> List[str]:
    dpy = Xlib.display.Display()
    resources = dpy.screen().root.xrandr_get_screen_resources()

    output_names = []

    for output in resources.outputs:
        output_info = dpy.xrandr_get_output_info(output, resources.config_timestamp)
        if output_info.connection == 0:
            output_names.append(output_info.name)

    return output_names


def set_gamma(output: str, gamma: float) -> None:
    logger.info("set_gamma %s %s", output, gamma)
    subprocess.call(["xrandr",
                     "--output", output,
                     "--gamma", "{}:{}:{}".format(gamma, gamma, gamma)])


def set_gamma_for_all(outputs: List[str], gamma: float) -> None:
    for output in outputs:
        set_gamma(output, gamma)


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Adjust gamma via systray icon")
    parser.add_argument("-d", "--debug", action='store_true', default=False,
                        help="Print lots of debugging output")
    return parser.parse_args(args)


def main(argv: List[str]) -> None:
    args = parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication([])
    trayicon = QSystemTrayIcon(QIcon.fromTheme("folder"))
    trayicon.setToolTip("Set Gamma")

    menu = QMenu()

    gammas = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0]

    outputs = get_outputs()

    submenu = menu.addMenu("All Outputs")
    for gamma in gammas:
        submenu.addAction("Gamma {}".format(gamma),
                          lambda gamma=gamma: set_gamma_for_all(outputs, gamma))

    for output in outputs:
        submenu = menu.addMenu(output)
        for gamma in gammas:
            submenu.addAction("Gamma {}".format(gamma),
                              lambda output=output, gamma=gamma: set_gamma(output, gamma))

    menu.addAction("Reset",
                   lambda gamma=gamma: set_gamma_for_all(outputs, 1.0))

    context_menu = QMenu()
    context_menu.addAction("Quit", lambda: app.quit())

    trayicon.setContextMenu(context_menu)

    def on_trayicon_activated(reason):
        if reason == QSystemTrayIcon.Trigger:
            rect = trayicon.geometry()
            menu.exec(rect.topLeft())

    trayicon.activated.connect(on_trayicon_activated)
    trayicon.show()
    app.exec()


def main_entrypoint() -> None:
    main(sys.argv)


# EOF #
