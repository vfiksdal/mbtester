;--------------------------------
; MBTester Installer
;--------------------------------
;General
!include "MUI2.nsh"
Name "MODBUS Tester"
OutFile "mbtester.exe"
Unicode True
InstallDir "$PROGRAMFILES64\$(^Name)"
RequestExecutionLevel admin
!include x64.nsh
ShowInstDetails show
!define MUI_ABORTWARNING

;--------------------------------
;Pages
    !insertmacro MUI_PAGE_LICENSE "LICENSE"
    !insertmacro MUI_PAGE_COMPONENTS
    !insertmacro MUI_PAGE_DIRECTORY
    !insertmacro MUI_PAGE_INSTFILES  

;--------------------------------
;Languages
    !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

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
SectionEnd

Section "MBTester GUI" MBTGUI
    DetailPrint "Installing MBTester GUI applications"
    ;SetOutPath $INSTDIR
    File "${__FILEDIR__}\mbtserver_gui.exe"
    File "${__FILEDIR__}\mbtclient_gui.exe"
SectionEnd

Section "MBTester CLI" MBTCLI
    DetailPrint "Installing MBTester CLI applications"
    ;SetOutPath $INSTDIR
    File "${__FILEDIR__}\mbtserver_cli.exe"
    File "${__FILEDIR__}\mbtclient_cli.exe"
SectionEnd

Section "Device definitions" MBTFiles
    DetailPrint "Installing MBTester device definitions"
    ;SetOutPath $INSTDIR
    File "${__FILEDIR__}\*.json"
SectionEnd

;--------------------------------
;Descriptions
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
