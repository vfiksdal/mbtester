##\package build
# \brief Builds binaries and installer for MS Windows
#
# Vegard Fiksdal (C) 2024
#
import PyInstaller.__main__
import shutil
from common import *

print('Deleting old build environment')
try:
    shutil.rmtree('build')
except:
    pass
try:
    shutil.rmtree('dist')
except:
    pass

print('Building v'+Utils.getAppVersion())
PyInstaller.__main__.run(['qmbtserver.py','--onefile','--noconsole','--icon','extras/mbtester.ico','--name','qmbtserver'])
PyInstaller.__main__.run(['qmbtclient.py','--onefile','--noconsole','--icon','extras/mbtester.ico','--name','qmbtclient'])
PyInstaller.__main__.run(['mbtserver.py','--onefile','--name','mbtserver'])
PyInstaller.__main__.run(['mbtclient.py','--onefile','--name','mbtclient'])

print('Copying accompanying files')
shutil.copy('extras/mbtester.ico','dist')
shutil.copy('README.md','dist')
shutil.copy('LICENSE','dist')
for file in os.listdir('.'):
    if file.upper().endswith('.JSON'):
        shutil.copy(file,'dist')

print('Archiving output files')
shutil.make_archive('mbtester-'+Utils.getAppVersion(), 'zip', 'dist')
shutil.move('mbtester-'+Utils.getAppVersion()+'.zip','dist')

print('Making installer')
nsispath = os.environ.get("PROGRAMFILES(X86)")+'\\NSIS\\makensis.exe'
if os.path.exists(nsispath):
    shutil.copy('extras\\mbtester.nsi','dist')
    os.system('"'+nsispath+'"'+' /NOCD dist\\mbtester.nsi')
    shutil.move('mbtester.exe','mbtester-'+Utils.getAppVersion()+'.exe')
    shutil.move('mbtester-'+Utils.getAppVersion()+'.exe','dist')
else:
    print('Could not find NSIS -- Skipping')

print('Cleaning house')
for file in os.listdir('.'):
    if file.upper().endswith('.SPEC'):
        os.unlink(file)

print('Done!')
