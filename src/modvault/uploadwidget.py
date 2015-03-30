#-------------------------------------------------------------------------------
# Copyright (c) 2012 Gael Honorez.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Public License v3.0
# which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/gpl.html
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
#-------------------------------------------------------------------------------



import urllib2
import tempfile
import zipfile
import os

from PyQt4 import QtCore, QtGui

import modvault
from util import datetostr,strtodate,now
import util

FormClass, BaseClass = util.loadUiType("modvault/upload.ui")


class UploadModWidget(FormClass, BaseClass):
    def __init__(self, parent, modDir, modinfo, *args, **kwargs):
        BaseClass.__init__(self, *args, **kwargs)

        self.setupUi(self)
        self.parent = parent
        self.client = self.parent.client
        self.modinfo = modinfo
        self.modDir = modDir
        #self.oldname = self.modinfo["name"]
        
        self.setStyleSheet(self.parent.client.styleSheet())
        
        self.setWindowTitle("Uploading Mod")

        self.Name.setText(modinfo.name)
        self.Version.setText(str(modinfo.version))
        if modinfo.ui_only: self.isUILabel.setText("is UI Only")
        else: self.isUILabel.setText("not UI Only")
        #self.UIOnly.setChecked(modinfo["ui_only"])
        self.UID.setText(modinfo.uid)
        self.Description.setPlainText(modinfo.description)
        if modinfo.icon != "":
            self.IconURI.setText(modvault.iconPathToFull(modinfo.icon))
            self.updateThumbnail()
        else:
            self.Thumbnail.setPixmap(util.pixmap("games/unknown_map.png"))
        #self.IconURI.returnPressed.connect(self.updateThumbnail)
        self.UploadButton.pressed.connect(self.upload)
        #self.IconDialogButton.pressed.connect(self.openicondialog)

    @QtCore.pyqtSlot()
    def upload(self):
        n = self.Name.text()
        if any([(i in n) for i in '"<*>|?/\\:']):
            QtGui.QMessageBox.information(self.client,"Invalid Name",
                        "The mod name contains invalid characters: /\\<>|?:\"")
            return


#        if not self.updateThumbnail():
#            QtGui.QMessageBox.information(self.client,"No thumbnail",
#                        "There is no thumbnail attached")
#            return

        #self.modinfo["name"] = n
        #self.modinfo["uid"] = self.UID.text()
        #self.modinfo["description"] = self.Description.toPlainText()
        #self.modinfo["version"] = int(self.Version.text())

        iconpath = modvault.iconPathToFull(self.modinfo.icon)
        #self.modinfo["name"] = n
        #self.modinfo["uid"] = self.UID.text()
        #self.modinfo["description"] = self.Description.toPlainText()
        #self.modinfo["version"] = int(self.Version.text())

        iconpath = modvault.iconPathToFull(self.modinfo.icon)
        infolder = False
        if iconpath != "" and os.path.commonprefix([os.path.normcase(self.modDir),os.path.normcase(iconpath)]) == os.path.normcase(self.modDir): #the icon is in the game folder
            localpath = modvault.fullPathToIcon(iconpath)
            infolder = True
        '''
        if self.oldname.lower() != self.modinfo["name"].lower(): # we need to change the name of the folder correspondingly
            try:
                os.rename(os.path.join(modvault.MODFOLDER, self.oldname),
                          os.path.join(modvault.MODFOLDER, self.modinfo["name"]))
                self.oldname = self.modinfo["name"]
            except:
                QtGui.QMessageBox.information(self.client,"Changing folder name",
                        "Because you changed the mod name, the folder name \
                         has to change as well. This failed.")
                return
            if infolder == True:
                iconpath = "/mods/" + self.modinfo["name"] +"/" + "/".join(localpath.split('/')[3:])
            self.modDir = os.path.join(modvault.MODFOLDER, self.modinfo["name"])
        '''
        if iconpath != "" and not infolder:
            QtGui.QMessageBox.information(self.client,"Invalid Icon File",
                        "The file %s is not located inside the modfolder. Copy the icon file to your modfolder and change the mod_info.lua accordingly" % iconpath)
            return
            '''
            newpath = os.path.join(self.modDir, os.path.split(iconpath)[1])
            f = open(iconpath, 'r')
            data = r.read()
            f.close()
            f = open(newpath, 'w')
            f.write(data)
            f.close()
            iconpath = modvault.fullPathToIcon(newpath)
        elif iconpath != "":
            iconpath = modvault.fullPathToIcon(iconpath)
        '''
        #self.modinfo["icon"] = iconpath
            
        #if not modvault.updateModInfo(self.modinfo["name"], self.modinfo):
        #    QtGui.QMessageBox.information(self.client,"Error updating Mod Info",
        #                "FAF could not read or write to the mod_info.lua file.")
        #    return
        
        try:
            temp = tempfile.NamedTemporaryFile(mode='w+b', suffix=".zip", delete=False)
            zipped = zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED)
            zipdir(self.modDir, zipped, os.path.basename(self.modDir))
            zipped.close()
            temp.flush()
        except:
            QtGui.QMessageBox.critical(self.client, "Mod uploading error", "Something went wrong zipping the mod files.")
            return
        qfile =QtCore.QFile(temp.name)

        self.modinfo.big = (self.SizeType.currentIndex() == 1)
        self.modinfo.small = (self.SizeType.currentIndex() == 2)
        
        #The server should check again if there is already a mod with this name or UID.
        self.client.writeToServer("UPLOAD_MOD", "%s.v%04d.zip" % (self.modinfo.name, self.modinfo.version), self.modinfo.to_dict(), qfile)
        
    '''
    @QtCore.pyqtSlot()
    def openicondialog(self):
        iconfilename = QtGui.QFileDialog.getOpenFileName(self.client, "Select an icon file", self.modDir,"Images (*.png *.jpg *.jpeg *.dds)")
        if iconfilename == "": return
        if os.path.splitext(iconfilename)[1].lower() == ".dds":
            old = iconfilename
            iconfilename = os.path.join(self.modDir, os.path.splitext(os.path.basename(iconfilename))[0] + ".png")
            succes = modvault.generateThumbnail(old,iconfilename)
            if not succes:
                logger.info("Could not write the png file for %s" % old)
                QtGui.QMessageBox.information(self.client,"Invalid Icon File",
                        "Because FAF can't read DDS files, it tried to convert it to a png. This failed. Try something else")
                return
        self.Thumbnail.setPixmap(util.pixmap(iconfilename, False))
        #except:
        #   QtGui.QMessageBox.information(self.client,"Invalid Icon File",
        #                "This was not a valid icon file. Please pick a png, jpeg or dds")
        #    return
        self.IconURI.setText(iconfilename)
    '''
    @QtCore.pyqtSlot()
    def updateThumbnail(self):
        iconfilename = modvault.iconPathToFull(self.modinfo.icon)
        if iconfilename == "":
            return False
        if os.path.splitext(iconfilename)[1].lower() == ".dds":
            old = iconfilename
            iconfilename = os.path.join(self.modDir, os.path.splitext(os.path.basename(iconfilename))[0] + ".png")
            succes = modvault.generateThumbnail(old,iconfilename)
            if not succes:
                logger.info("Could not write the png file for %s" % old)
                QtGui.QMessageBox.information(self.client,"Invalid Icon File",
                        "Because FAF can't read DDS files, it tried to convert it to a png. This failed. Try something else")
                return False
        try:
            self.Thumbnail.setPixmap(util.pixmap(iconfilename,False))
        except:
            QtGui.QMessageBox.information(self.client,"Invalid Icon File",
                        "This was not a valid icon file. Please pick a png or jpeg")
            return False
        self.modinfo.thumbnail = modvault.fullPathToIcon(iconfilename)
        self.IconURI.setText(iconfilename)
        return True
    

#from http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory-in-python
def zipdir(path, zipf, fname):
    '''zips the entire directory path to zipf. Every file in the zipfile starts with fname.
    So if path is "/foo/bar/hello" and fname is "test" then every file in zipf is of the form "/test/*.*"'''
    path = os.path.normcase(path)
    if path[-1] in r'\/':
        path = path[:-1]
    short = os.path.split(path)[0]
    for root, dirs, files in os.walk(path):
        for f in files:
            name = os.path.join(os.path.normcase(root), f)
            n = name[len(os.path.commonprefix([name,path])):]
            if n[0] == "\\": n = n[1:]
            zipf.write(name, os.path.join(fname,n))

