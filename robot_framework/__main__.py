"""The entry point of the process."""

# Remember to delete this error
# raise NotImplementedError("Remember to choose a framework to use.")

# from robot_framework import linear_framework
# linear_framework.main()

from robot_framework import queue_framework
from robot_framework.paragraf8 import ruting as paragraf8_ruting

# Diagnose-tilstand for §8: skriver blankettens feltstruktur i loggen uden at
# roere koeen eller SharePoint. Se robot_framework/paragraf8/diagnostik.py.
if paragraf8_ruting.struktur_oensket():
    from robot_framework.paragraf8 import diagnostik as paragraf8_diagnostik
    paragraf8_diagnostik.main()
else:
    queue_framework.main()
