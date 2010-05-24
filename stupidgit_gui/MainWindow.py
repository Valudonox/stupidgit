# -*- coding: utf-8
from git import *
from HistoryTab import HistoryTab
from IndexTab import IndexTab
import wx
from wx import xrc
from wxutil import *

STUPIDGIT_VERSION = "v0.1.1"

ID_NEWWINDOW    = 101
ID_CLOSEWINDOW  = 102

TAB_HISTORY     = 0
TAB_INDEX       = 1

license_text = u'''
Copyright (c) 2009 Ákos Gyimesi

Permission is hereby granted, free of charge, to
any person obtaining a copy of this software and
associated documentation files (the "Software"),
to deal in the Software without restriction,
including without limitation the rights to use,
copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is
furnished to do so, subject to the following
conditions:

The above copyright notice and this permission
notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY
OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
'''

class MainWindow(object):
    def __init__(self, repo):
        # Load frame from XRC
        self.frame = LoadFrame(None, 'MainWindow')
        wx.TheApp.app_windows.append(self)
        
        # Read default window size
        self.config = wx.Config('stupidgit')
        width = self.config.ReadInt('MainWindowWidth', 550)
        height = self.config.ReadInt('MainWindowHeight', 650)
        self.frame.SetSize((width, height))
        
        # Create module choice
        toolbar = self.frame.GetToolBar()
        self.moduleChoice = wx.Choice(toolbar, -1)
        if sys.platform == 'darwin':
            # Don't ask me why, but that's how the control is positioned to middle...
            self.moduleChoice.SetSize((200,15))
        else:
            self.moduleChoice.SetSize((200,-1))
        
        self.moduleChoice.Bind(wx.EVT_CHOICE, self.OnModuleChosen)
        toolbar.InsertControl(0, self.moduleChoice)
        toolbar.Realize()
        
        # Setup events
        SetupEvents(self.frame, [
            (None, wx.EVT_WINDOW_CREATE, self.OnWindowCreated),
            (None, wx.EVT_CLOSE, self.OnWindowClosed),
            
            ('tabs', wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTabChanged),

            ('quitMenuItem', wx.EVT_MENU, self.OnExit),
            ('openMenuItem', wx.EVT_MENU, self.OnOpenRepository),
            ('newWindowMenuItem', wx.EVT_MENU, self.OnNewWindow),
            ('closeWindowMenuItem', wx.EVT_MENU, self.OnCloseWindow),
            ('aboutMenuItem', wx.EVT_MENU, self.OnAbout),
            ('refreshMenuItem', wx.EVT_MENU, self.OnRefresh),

            ('refreshTool', wx.EVT_TOOL, self.OnRefresh),
            ('refreshButton', wx.EVT_BUTTON, self.OnRefresh),
        ])
        
        # Setup tabs
        self.historyTab = HistoryTab(self)
        self.indexTab = IndexTab(self)
        self.selectedTab = 0

        # Load repository
        self.SetMainRepo(repo)

    def Show(self, doShow=True):
        self.frame.Show(doShow)

    def OnNewWindow(self, e):
        win = MainWindow(None)
        win.Show(True)

    def OnWindowCreated(self, e):
        self.indexTab.OnCreated()
        self.historyTab.OnCreated()

    def OnCloseWindow(self, e):
        self.frame.Close()

    def OnWindowClosed(self, e):
        # Save window geometry
        size = self.frame.GetSize()
        self.config.WriteInt('MainWindowWidth', size.GetWidth())
        self.config.WriteInt('MainWindowHeight', size.GetHeight())
        self.historyTab.SaveState()
        self.indexTab.SaveState()

        # Close window
        wx.TheApp.app_windows.remove(self)
        self.frame.Destroy()

    def OnOpenRepository(self, e):
        repodir = wx.DirSelector("Open repository")
        if not repodir: return

        try:
            repo = Repository(repodir)

            if self.mainRepo:
                new_win = MainWindow(repo)
                new_win.Show(True)
            else:
                self.SetMainRepo(repo)
        except GitError, msg:
            wx.MessageBox(str(msg), 'Error', style=wx.OK|wx.ICON_ERROR)

    def OnTabChanged(self, e):
        self.selectedTab = e.GetSelection()

    def OnAbout(self, e):
        info = wx.AboutDialogInfo()
        info.SetName("stupidgit")
        info.SetDescription("A cross-platform git GUI with strong submodule support.\n\nHomepage: http://github.com/gyim/stupidgit")
        info.SetVersion(STUPIDGIT_VERSION)
        info.SetCopyright(u"(c) Ákos Gyimesi, 2009.")
        info.SetLicense(license_text)

        wx.AboutBox(info)

    def OnExit(self, e):
        while wx.TheApp.app_windows:
            wx.TheApp.app_windows[0].frame.Close(True)
        wx.TheApp.ExitMainLoop()

    def SetMainRepo(self, repo):
        self.mainRepo = repo

        if repo:
            title = "stupidgit - %s" % os.path.basename(repo.dir)

            for module in self.mainRepo.all_modules:
                self.moduleChoice.Append(module.name)
            
            self.moduleChoice.Select(0)
            self.SetRepo(repo)

        else:
            title = "stupidgit"
            self.currentRepo = None

        self.frame.SetTitle(title)

    def SetRepo(self, repo):
        self.currentRepo = repo
        self.currentRepo.load_refs()
        self.historyTab.SetRepo(repo)
        self.indexTab.SetRepo(repo)

    def ReloadRepo(self):
        self.currentRepo.load_refs()
        self.SetRepo(self.currentRepo)

        # Load referenced version in submodules
        for submodule in self.currentRepo.submodules:
            submodule.load_refs()

    def OnModuleChosen(self, e):
        module_name = e.GetString()
        module = [m for m in self.mainRepo.all_modules if m.name == module_name]
        if module:
            self.SetRepo(module[0])

    def OnRefresh(self, e):
        self.currentRepo.load_refs()
        self.SetRepo(self.currentRepo)

