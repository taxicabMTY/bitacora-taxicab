# Instala el envío automático de la bitácora en Windows (Programador de tareas).
# Uso, desde PowerShell, dentro de esta carpeta:
#     powershell -ExecutionPolicy Bypass -File .\instalar_windows.ps1
# Para quitarlo:
#     powershell -ExecutionPolicy Bypass -File .\instalar_windows.ps1 -Desinstalar
param([switch]$Desinstalar, [string]$Hora = "08:20")

$ErrorActionPreference = "Stop"
$destino = Join-Path $env:LOCALAPPDATA "TaxiCab-Bitacora"
$tareas = @("TaxiCab Bitacora diaria", "TaxiCab Bitacora semanal")

if ($Desinstalar) {
    foreach ($t in $tareas) { Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue }
    Write-Host "Tareas quitadas. La carpeta $destino se queda (ahí está tu .env); bórrala a mano si quieres."
    return
}

$python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $python) { throw "No encontré Python. Instálalo desde https://www.python.org/downloads/ (marca 'Add python.exe to PATH')." }

# Copia el script a una carpeta fija: así sigue funcionando aunque cambies de rama en el repo.
New-Item -ItemType Directory -Force -Path $destino | Out-Null
Copy-Item (Join-Path $PSScriptRoot "enviar_bitacora.py") $destino -Force
$envDestino = Join-Path $destino ".env"
if (-not (Test-Path $envDestino)) {
    $envOrigen = Join-Path $PSScriptRoot ".env"
    if (Test-Path $envOrigen) { Copy-Item $envOrigen $envDestino }
    else {
        Copy-Item (Join-Path $PSScriptRoot ".env.example") $envDestino
        Write-Host "Se creó $envDestino vacío. Llénalo con tus datos antes de la primera corrida."
    }
}

$script = Join-Path $destino "enviar_bitacora.py"
# StartWhenAvailable: si el equipo estaba apagado o dormido a la hora, corre al encenderse.
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

$accionDiaria = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" diaria" -WorkingDirectory $destino
$accionSemanal = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" semanal" -WorkingDirectory $destino
Register-ScheduledTask -TaskName $tareas[0] -Action $accionDiaria -Settings $ajustes `
    -Trigger (New-ScheduledTaskTrigger -Daily -At $Hora) -Force | Out-Null
Register-ScheduledTask -TaskName $tareas[1] -Action $accionSemanal -Settings $ajustes `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $Hora) -Force | Out-Null

Write-Host "Listo. Diaria: todos los días a las $Hora. Semanal: lunes a las $Hora."
Write-Host "Prueba manual:  & '$python' '$script' diaria"
