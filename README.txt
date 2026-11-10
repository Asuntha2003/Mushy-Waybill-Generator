MUSHY CUTE CORNER - WAYBILL GENERATOR

You want to use this program on Windows WITHOUT installing Python.
The Windows EXE is built automatically using GitHub Actions. Python is only
installed on GitHub's temporary build machine, not on your computer.

GET YOUR STANDALONE WINDOWS EXE
1. Sign in to https://github.com (create a free account if needed).
2. Create a new repository, for example: mushy-waybill-generator.
3. Upload all files and folders from this project ZIP to the repository.
   Make sure the .github/workflows/build-windows.yml file is included.
4. Open the repository's Actions tab.
5. Select "Build Windows EXE" and click "Run workflow" if it has not started
   automatically after upload.
6. Wait for the workflow to finish successfully.
7. Open the completed workflow run. Under Artifacts, download
   "MushyWaybill-Windows".
8. Extract that downloaded ZIP. It contains MushyWaybill.exe.
9. Copy MushyWaybill.exe to a normal folder on your Windows PC and double-click it.

USING THE APP
- No Python installation is required on the computer that runs MushyWaybill.exe.
- The program creates database and generated_waybills folders beside the EXE.
- Keep the EXE and those folders together. Back them up to preserve records.
- If Windows SmartScreen warns about an unrecognized app, only run it if you
  downloaded it from your own trusted build/repository.

PROJECT CONTENTS
- waybill.py: application source
- requirements.txt: dependencies
- BUILD_EXE.bat: optional local build method (requires Python)
- .github/workflows/build-windows.yml: cloud Windows EXE build recipe

PRINTING
The generated PDF page is 4 x 6 inches (101.6 x 152.4 mm).
In the PDF viewer/printer settings choose 4 x 6 inch paper and Actual Size / 100%.

NOTE
This is a general courier waybill generator. It is not connected to any courier
company's booking, barcode, or tracking service.
