from PyInstaller.__main__ import run

if __name__ == "__main__":
    run([
        'main.py',
        '--onefile',
        '--windowed',  # This prevents the console from opening
        '--name=Rotgym-StyleBulletHell',
        '--icon=icon.ico'  # Ensure the path is correct
    ])
