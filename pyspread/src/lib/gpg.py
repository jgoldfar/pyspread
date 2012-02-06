#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

gpg
===

GPG handling functions

Provides
--------

 * is_pyme_present: Checks if pyme is installed
 * genkey: Generates gpg key
 * sign: Returns detached signature for file
 * verify: verifies stream against signature

"""

import sys

import wx
import wx.lib.agw.genericmessagedialog as GMD

from src.config import config
from src.gui._dialogs import GPGParamsDialog

from pyme import core, pygpgme, errors
import pyme.errors


def _passphrase_callback(hint='', desc='', prev_bad=''):
    """Callback function needed by pyme"""

    return config["gpg_key_passphrase"]


def _get_file_data(filename):
    """Returns pyme.core.Data object of file."""

    # Required because of unicode bug in pyme

    infile = open(filename, "rb")
    infile_content = infile.read()
    infile.close()

    return core.Data(string=infile_content)


def choose_uid(context):
    """Displays gpg key choice and returns uid name or None on Cancel"""

    gpg_uids = []
    uid_strings = []

    for key in context.op_keylist_all("", 0):
        if key.can_sign and key.owner_trust and not key.invalid:
            for uid in key.uids:
                uid_data = uid.uid, uid.name, uid.email, uid.comment
                gpg_uids.append(uid.name)
                uid_strings.append("\t".join(uid_data))

    dlg = wx.SingleChoiceDialog(
            None,
            'Choose a GPG key that you own for signing pyspread save files.\n'
            'Pressing Cancel creates a new key.',
            'Choose key',
            uid_strings, wx.CHOICEDLG_STYLE,
            )

    if dlg.ShowModal() == wx.ID_OK:
        uid = gpg_uids[uid_strings.index(dlg.GetStringSelection())]

    else:
        uid = None

    dlg.Destroy()

    return uid


def get_key_params_string(params):
    """Returns parameter string from given params dict"""

    param_head = '<GnupgKeyParms format="internal">'
    param_foot = '</GnupgKeyParms>'

    param_str_list = [param_head, param_foot]

    for param in params[::-1]:
        param_str_list.insert(1, ": ".join(param))

    return str("\n".join(param_str_list))


def get_key_params_from_user():
    """Displays parameter entry dialog and returns parameter string"""

    gpg_key_parameters = [ \
        ('Key-Type', 'DSA'),
        ('Key-Length', '2048'),
        ('Subkey-Type', 'ELG-E'),
        ('Subkey-Length', '2048'),
        ('Expire-Date', '0'),
    ]

    PASSWD = True
    NO_PASSWD = False

    params = [ \
        ['Real name', 'Name-Real', NO_PASSWD],
        ['Passphrase', 'Passphrase', PASSWD],
        ['E-mail', 'Name-Email', NO_PASSWD],
        ['Comment', 'Name-Comment', NO_PASSWD],
    ]

    vals = [""] * len(params)

    while "" in vals:
        dlg = GPGParamsDialog(None, -1, "Enter GPG key parameters", params)
        dlg.CenterOnScreen()

        for val, textctrl in zip(vals, dlg.textctrls):
            textctrl.SetValue(val)

        if dlg.ShowModal() != wx.ID_OK:
            sys.exit()

        vals = [textctrl.Value for textctrl in dlg.textctrls]

        dlg.Destroy()

        if "" in vals:
            msg = "Please enter a value in each field."

            dlg = GMD.GenericMessageDialog(None, msg, "Missing value",
                                           wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    for (_, key, _), val in zip(params, vals):
        gpg_key_parameters.insert(-2, (key, val))

    return gpg_key_parameters


def get_gpg_passwd():
    """Opens a dialog for a GPG password and returns the password or None"""

    dlg = wx.TextEntryDialog(None, 'Please enter your GPG key passphrase.\n' \
            'Note that it will be stored as clear text in .pyspreadrc',
            'GPG key passphrase', '', style=wx.TE_PASSWORD | wx.OK)

    if dlg.ShowModal() == wx.ID_OK:
        dlg.Destroy()
        return dlg.GetValue()

    dlg.Destroy()


def genkey():
    """Creates a new standard GPG key"""

    # Initialize our context.
    core.check_version(None)

    context = core.Context()
    context.set_armor(1)

    # Check if standard key is already present
    keyname = config["gpg_key_uid"]
    context.op_keylist_start(keyname, 0)
    key = context.op_keylist_next()

    # If no key is chosen generate one

    if key is None or not key:
        # If no GPG key is set in config, choose one

        uid = choose_uid(context)

    if (key is None or not key) and uid is not None:
        config["gpg_key_uid"] = repr(uid)
        passwd = get_gpg_passwd()

        if passwd is None:
            sys.exit()
        else:
            config["gpg_key_passphrase"] = repr(passwd)

    elif (key is None or not key) and uid is None:

        # Key not present --> Create new one

        # Show progress dialog

        dlg = wx.ProgressDialog("GPG key generation",
                               "Generating new GPG key " + keyname + \
                               ".\nThis may take some time.\n \n" + \
                               "Progress bar may stall. Please wait.",
                               maximum=200,
                               parent=None,
                               style=wx.PD_ELAPSED_TIME)

        class CBFs(object):
            """Callback functions for pyme"""

            progress = 0

            def cbf(self, what=None, type=None, current=None, total=None,
                    hook=None):
                """Callback function that updates progress dialog"""

                dlg.Update(self.progress % 199)
                self.progress += 1

        cbfs = CBFs()

        gpg_key_parameters = get_key_params_from_user()

        config["gpg_key_uid"] = repr(str( \
            [val for key, val in gpg_key_parameters if key == 'Name-Real'][0]))
        config["gpg_key_passphrase"] = repr(str(([val \
            for key, val in gpg_key_parameters if key == 'Passphrase'][0])))

        gpg_key_parameters_string = get_key_params_string(gpg_key_parameters)

        context.set_progress_cb(cbfs.cbf, None)

        context.op_genkey(gpg_key_parameters_string, None, None)

        dlg.Destroy()


def sign(filename):
    """Returns detached signature for file"""

    plaintext = _get_file_data(filename)

    ciphertext = core.Data()

    ctx = core.Context()

    ctx.set_armor(1)
    ctx.set_passphrase_cb(_passphrase_callback)

    ctx.op_keylist_start(config["gpg_key_uid"], 0)
    sigkey = ctx.op_keylist_next()
    ##print sigkey.uids[0].uid

    ctx.signers_clear()
    ctx.signers_add(sigkey)

    passwd_is_incorrect = True

    while passwd_is_incorrect:
        try:
            ctx.op_sign(plaintext, ciphertext, pygpgme.GPGME_SIG_MODE_DETACH)
            passwd_is_incorrect = False

        except errors.GPGMEError:
            passwd = get_gpg_passwd()
            if passwd is None:
                return

            config["gpg_key_passphrase"] = repr(passwd)
            ctx.set_passphrase_cb(_passphrase_callback)

    ciphertext.seek(0, 0)
    signature = ciphertext.read()

    return signature


def verify(sigfilename, filefilename=None):
    """Verifies a signature, returns True if successful else False."""

    context = core.Context()

    # Create Data with signed text.
    __signature = _get_file_data(sigfilename)

    if filefilename:
        __file = _get_file_data(filefilename)
        __plain = None
    else:
        __file = None
        __plain = core.Data()

    # Verify.
    try:
        context.op_verify(__signature, __file, __plain)
    except pyme.errors.GPGMEError:
        return False

    result = context.op_verify_result()

    # List results for all signatures. Status equal 0 means "Ok".
    validation_sucess = False

    for signature in result.signatures:
        if (not signature.status) and signature.validity:
            validation_sucess = True

    return validation_sucess