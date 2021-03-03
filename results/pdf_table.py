#!/home/hasanb/anaconda3/bin/python
import pylatex as pl
import sys
from os.path import join

fnames = sys.argv[1:]

for fname in fnames:
    with open(fname) as f:
        content = f.read()

    doc = pl.Document()
    doc.packages.append(pl.Package('booktabs'))
    doc.packages.append(pl.Package('multirow'))

    with doc.create(pl.Table(position='htbp')) as table:
        table.append(pl.Command('centering'))
        table.append(pl.NoEscape(content))

    doc.generate_pdf(join('..', fname.split('.')[0]), clean_tex=False)
