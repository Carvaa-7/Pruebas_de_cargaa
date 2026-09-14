param([string]$Pptx, [string]$OutDir, [string]$Only = "")
New-Item -ItemType Directory -Force $OutDir | Out-Null
$app = New-Object -ComObject PowerPoint.Application
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow)
    $pres = $app.Presentations.Open($Pptx, -1, 0, 0)
    $n = $pres.Slides.Count
    $sel = if ($Only) { $Only.Split(',') | ForEach-Object { [int]$_ } } else { 1..$n }
    foreach ($i in $sel) {
        $pres.Slides.Item($i).Export((Join-Path $OutDir ("s{0:D2}.png" -f $i)), "PNG", 1600, 900)
    }
    "exportadas: $($sel.Count) de $n"
    $pres.Close()
} finally {
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
