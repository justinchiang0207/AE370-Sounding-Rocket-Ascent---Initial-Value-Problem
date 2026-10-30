"""Shared, colorblind-conscious figure styling and vector/raster export."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
COLORS = ['#204E70', '#C07824', '#4D8272']

def setup():
    plt.rcParams.update({
        'font.size': 10, 'axes.labelsize': 10, 'axes.titlesize': 10,
        'legend.fontsize': 9, 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.prop_cycle': plt.cycler(color=COLORS),
        'savefig.dpi': 220, 'pdf.fonttype': 42,
        'axes.grid': True, 'grid.alpha': .2,
    })

def save(fig, name):
    (ROOT / 'figures').mkdir(exist_ok=True)
    fig.savefig(ROOT / f'figures/{name}.png', dpi=220, bbox_inches='tight')
    fig.savefig(ROOT / f'figures/{name}.pdf', bbox_inches='tight')
    plt.close(fig)
