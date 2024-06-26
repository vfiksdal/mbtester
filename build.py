##\package build
# \brief Builds binaries and installer for MS Windows
#
# Vegard Fiksdal (C) 2024
#
import PyInstaller.__main__
import shutil,sys
from common import *

def preclean():
    print('Deleting old build environment')
    try:
        shutil.rmtree('build')
    except:
        pass
    try:
        shutil.rmtree('dist')
    except:
        pass

def build_bin():
    print('Building v'+App.getVersion())
    PyInstaller.__main__.run(['qmbtester.py','--onefile','--noconsole','--icon','extras/mbtester.ico','--name','qmbtester'])
    PyInstaller.__main__.run(['mbtester.py','--onefile','--name','mbtester'])

    print('Copying accompanying files')
    shutil.copy('extras/mbtester.ico','dist')
    shutil.copy('README.md','dist')
    shutil.copy('LICENSE','dist')
    for file in os.listdir('.'):
        if file.upper().endswith('.JSON'):
            shutil.copy(file,'dist')

def build_zip():
    print('Archiving output files')
    shutil.make_archive('mbtester-'+App.getVersion(), 'zip', 'dist')
    #shutil.move('mbtester-'+App.getVersion()+'.zip','dist')

def build_installer():
    print('Making installer')
    nsispath = os.environ.get("PROGRAMFILES(X86)")+'\\NSIS\\makensis.exe'
    if os.path.exists(nsispath):
        shutil.copy('extras\\mbtester.nsi','dist')
        os.system('"'+nsispath+'"'+' /NOCD dist\\mbtester.nsi')
        shutil.move('mbtester.exe','mbtester-'+App.getVersion()+'.exe')
        #shutil.move('mbtester-'+App.getVersion()+'.exe','dist')
    else:
        print('Could not find NSIS -- Skipping')

def postclean():
    print('Cleaning intermediary files')
    for file in os.listdir('.'):
        if file.upper().endswith('.SPEC'):
            os.unlink(file)

def mrproper():
    os.system('git clean -d -x -n')
    if input('Type yes to confirm: ').upper()=='YES':
        os.system('git clean -d -x -f')
    else:
        print('Deep clean was skipped')

    print('Ivalid build parameter: '+arg)
    print('Use '+sys.argv[0]+' --help for usage information')
if len(sys.argv)==2:
    arg=sys.argv[1]
else:
    print('Ivalid build parameters: '+str(sys.argv[1:]))
    print('')
    arg='--help'

if arg=='--build':
    preclean()
    build_bin()
    postclean()
elif arg=='--archive':
    preclean()
    build_bin()
    build_zip()
    postclean()
elif arg=='--release':
    preclean()
    build_bin()
    build_installer()
    postclean()
elif arg=='--all':
    preclean()
    build_bin()
    build_zip()
    build_installer()
    postclean()
elif arg=='--clean':
    preclean()
    postclean()
elif arg=='--mrproper':
    mrproper()
elif arg=='--help':
    print('MBTester build script')
    print('Usage: '+sys.argv[0]+' SWITCH')
    print('')
    print('Switches:')
    print('\t--build\t\tBuild windows binaries')
    print('\t--release\tBuild windows installer')
    print('\t--archive\tBuild windows binaries and zip them')
    print('\t--all\t\tBuild windows installer and zip archive')
    print('\t--clean\t\tClean build directories')
    print('\t--mrproper\tClean up repo')
    print('')
else:
    print('Ivalid build parameter: '+arg)
    print('Use '+sys.argv[0]+' --help for usage information')
