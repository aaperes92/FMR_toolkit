"""Lanza la interfaz gráfica:  python -m fmrtoolkit.gui

El backend de matplotlib se fija en 'Agg' ANTES de importar cualquier módulo del
toolkit: así los cálculos (que corren en un hilo aparte y usan pyplot) nunca crean
ventanas ni tocan Tk. Las figuras se muestran en el hilo principal con
FigureCanvasTkAgg (ver gui/graficos.py).
"""

import matplotlib

matplotlib.use('Agg')

from fmrtoolkit.gui.app import main  # noqa: E402  (después de fijar el backend)

if __name__ == '__main__':
    main()
