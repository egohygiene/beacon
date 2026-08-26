# type "make" command in Unix to create asme2e.pdf file
.PHONY: all abstract clean test

all:
	latex asme2e
	bibtex asme2e
	latex asme2e
	latex asme2e
	dvips -o asme2e.ps asme2e
	ps2pdf asme2e.ps asme2e.pdf

abstract:
	latex abstract
	dvips -o abstract.ps abstract
	ps2pdf abstract.ps abstract.pdf

test: all

clean:
	(rm -rf *.ps *.log *.dvi *.aux *.*% *.lof *.lop *.lot *.toc *.idx *.ilg *.ind *.bbl *blg)
