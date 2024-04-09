@echo off
@echo -----------Installing GIMP-ML-----------
python -m pip install virtualenv
if not exist "gimpenv3" (
    @echo Creating virtual environment gimpenv3...
    python -m venv gimpenv3
    if errorlevel 1 (
        @echo Error creating the virtual environment. Please check your Python installation.
        exit /b 1
    )
)
@echo Activating virtual gimpenv3...
@call .\gimpenv3\Scripts\activate
if errorlevel 1 (
    @echo Error activating the virtual environment. Please make sure it's correctly set up.
    exit /b 1
)
@powershell -ExecutionPolicy Bypass -Command "$_=((Get-Content \"%~f0\") -join \"`n\");iex $_.Substring($_.IndexOf(\"goto :\"+\"EOF\")+9)"
@goto :EOF

param([switch]$cpuonly = $false)

if (!((Get-Command python).Path | Select-String -Pattern gimpenv3 -Quiet)) {
    throw "Failed to activate the created environment."
}
if ($cpuonly) {
    gimpenv3\Scripts\python.exe -m pip install torch torchvision torchaudio
} else {
    gimpenv3\Scripts\python.exe -m pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116
    gimpenv3\Scripts\python.exe -m pip install cudatoolkit
}

gimpenv3\Scripts\python.exe -m pip install -r requirements.txt
gimpenv3\Scripts\python.exe -m pip install -e .
gimpenv3\Scripts\python.exe gimpml/init_config.py
# Register the plugins directory in GIMP settings
$pluginsDir = [IO.Path]::GetFullPath(".\gimpml\plugins")
$gimpdir = Get-ChildItem -Filter "GIMP*" -Directory -ErrorAction SilentlyContinue -Path "C:\Program Files\" |
    Where-Object { $_.Name -match '^(GIMP 2\.9|GIMP 3)' } |
    Select-Object -ExpandProperty FullName
$gimp = (dir  "$($gimpdir)\bin\gimp-console-*.exe") |
     Where-Object { $_.Name -match '\d+\.\d+' } |
     Select-Object -First 1 -ExpandProperty FullName
if (!($gimp -and (Test-Path $gimp))) {
    throw "Could not find GIMP! You will have to add '$pluginsDir' to Preferences -> Folders -> Plug-ins manually."
}
$version = (& $gimp --version | Select-String -Pattern [[32]\.\d+).Matches.Value
if (!($version)) {
    throw "Could not determine GIMP version."
}
$gimprcPath = ($env:APPDATA + '\GIMP\' + $version + '\gimprc')
$escapedDir = [regex]::escape($pluginsDir)
if (!(Test-Path $gimprcPath)) {
    New-Item $gimprcPath -Force
}
if (!(Select-String -Path $gimprcPath -Pattern 'plug-in-path' -Quiet)) {
    (cat $gimprcPath) + ('(plug-in-path "${gimp_dir}\\plug-ins;${gimp_plug_in_dir}\\plug-ins;' + $escapedDir + '")') | Set-Content $gimprcPath
} elseif (!(Select-String -Path $gimprcPath -Pattern ([regex]::escape($escapedDir)) -Quiet)) {
    (cat $gimprcPath) -replace '\(\s*plug-in-path\s+"', ('$0' + $escapedDir + ';') | Set-Content $gimprcPath
}

echo "-----------Installed GIMP-ML------------"
