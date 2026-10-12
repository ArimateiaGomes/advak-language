$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$dir\advak.py" @args
