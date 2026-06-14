name: Build Windows Executable

# ------------------------------------------------------------
# Builds a standalone Windows .exe of the SGS School Manager
# using PyInstaller.
#
# Triggers:
#   - On every push to main/master (build + upload artifact)
#   - On every pull request (build only, for validation)
#   - On version tags (vX.Y.Z) -> also publish a GitHub Release
#   - Manually via "Run workflow" (workflow_dispatch)
# ------------------------------------------------------------

on:
  push:
    branches: [ "main", "master" ]
    tags: [ "v*.*.*" ]
  pull_request:
    branches: [ "main", "master" ]
  workflow_dispatch: {}

jobs:
  build-windows-exe:
    name: Build Windows .exe
    runs-on: windows-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-build.txt

      - name: Build executable with PyInstaller
        run: |
          pyinstaller --noconfirm build.spec

      - name: Verify build output
        run: |
          dir dist

      - name: Upload executable artifact
        uses: actions/upload-artifact@v4
        with:
          name: SGS_School_Manager-windows
          path: |
            dist/SGS_School_Manager.exe
          if-no-files-found: error
          retention-days: 30

      - name: Package release zip (with data folders)
        if: startsWith(github.ref, 'refs/tags/')
        shell: pwsh
        run: |
          New-Item -ItemType Directory -Force -Path release/SGS_School_Manager
          Copy-Item dist/SGS_School_Manager.exe release/SGS_School_Manager/
          Copy-Item -Recurse database release/SGS_School_Manager/data/database -Force
          Copy-Item -Recurse exports release/SGS_School_Manager/data/exports -Force
          Copy-Item -Recurse backups release/SGS_School_Manager/data/backups -Force
          Copy-Item -Recurse sample_data release/SGS_School_Manager/data/sample_data -Force
          Copy-Item -Recurse assets release/SGS_School_Manager/data/assets -Force
          Copy-Item README.md release/SGS_School_Manager/
          Copy-Item INSTALLATION.md release/SGS_School_Manager/
          Remove-Item -Force release/SGS_School_Manager/data/database/school.db -ErrorAction SilentlyContinue
          Compress-Archive -Path release/SGS_School_Manager/* -DestinationPath SGS_School_Manager_Windows.zip

      - name: Create GitHub Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v2
        with:
          files: SGS_School_Manager_Windows.zip
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
