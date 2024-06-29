;--------------------------------
; MBTester Installer
;--------------------------------
;General
!include "MUI2.nsh"
!define REGPATH_UNINSTSUBKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)"
Name "MODBUS Tester"
OutFile "mbtester.exe"
Unicode True
InstallDir "$PROGRAMFILES64\$(^Name)"
InstallDirRegKey HKLM "${REGPATH_UNINSTSUBKEY}" "UninstallString"
RequestExecutionLevel admin
!include x64.nsh
ShowInstDetails show
!define MUI_ICON ${__FILEDIR__}\mbtester.ico
!define MUI_ABORTWARNING
Var StartMenuFolder

;--------------------------------
;Pages
;--------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES  
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
;--------------------------------
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections
;--------------------------------
Section "MBTester core" MBTBase
    SectionIn RO
    DetailPrint "Installing MBTester core"
    SetOutPath $INSTDIR
    EnVar::Check "PATH" "$INSTDIR"
    Pop $0
    ${If} $0 != 0
        EnVar::AddValue "PATH" "$INSTDIR"
    ${EndIf}
    File "${__FILEDIR__}\README.md"
    File "${__FILEDIR__}\LICENSE"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" "DisplayName" "MODBUS Test Utilities"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$(^Name)" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
SectionEnd

Section "MBTester GUI" MBTGUI
    DetailPrint "Installing MBTester GUI applications"
    File "${__FILEDIR__}\qmbtester.exe"
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\MBTServer.lnk" "$INSTDIR\qmbtester.exe" "--server"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\MBTClient.lnk" "$INSTDIR\qmbtester.exe" "--client"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\MBTProxy.lnk" "$INSTDIR\qmbtester.exe" "--server --client"
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "MBTester CLI" MBTCLI
    DetailPrint "Installing MBTester CLI applications"
    File "${__FILEDIR__}\mbtester.exe"
SectionEnd

Section "Device definitions" MBTFiles
    DetailPrint "Installing MBTester device definitions"
    File "${__FILEDIR__}\*.json"
SectionEnd

;--------------------------------
; Uninstaller
;--------------------------------
Section -Uninstall
    Delete "$INSTDIR\qmbtester.exe"
    Delete "$INSTDIR\mbtester.exe"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\*.json"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    RMDir "$INSTDIR"
    DeleteRegKey HKLM "${REGPATH_UNINSTSUBKEY}"
    EnVar::Check "PATH" "$INSTDIR"
    Pop $0
    ${If} $0 == 0
        EnVar::DeleteValue "PATH" "$INSTDIR"
    ${EndIf}
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    Delete "$SMPROGRAMS\$StartMenuFolder\MBTServer.lnk"
    Delete "$SMPROGRAMS\$StartMenuFolder\MBTClient.lnk"
    Delete "$SMPROGRAMS\$StartMenuFolder\MBTProxy.lnk"
    RMDir "$SMPROGRAMS\$StartMenuFolder"
SectionEnd

;--------------------------------
; Descriptions
;--------------------------------
LangString DESC_MBTBase ${LANG_ENGLISH} "MBTester"
LangString DESC_MBTGUI ${LANG_ENGLISH} "GUI applications"
LangString DESC_MBTCLI ${LANG_ENGLISH} "Commandline applications"
LangString DESC_MBTFiles ${LANG_ENGLISH} "MODBUS Device definitions"

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${MBTBase} $(DESC_MBTBase)
    !insertmacro MUI_DESCRIPTION_TEXT ${MBTGUI} $(DESC_MBTGUI)
    !insertmacro MUI_DESCRIPTION_TEXT ${MBTCLI} $(DESC_MBTCLI)
    !insertmacro MUI_DESCRIPTION_TEXT ${MBTFiles} $(DESC_MBTFiles)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
