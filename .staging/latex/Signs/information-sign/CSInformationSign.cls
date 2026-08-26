%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Information Sign
% LaTeX Class
% Version 1.1 (February 25, 2022)
%
% This class originates from:
% https://www.LaTeXTemplates.com
%
% Author:
% Vel (vel@latextemplates.com)
%
% License:
% CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%----------------------------------------------------------------------------------------
%	CLASS CONFIGURATION
%----------------------------------------------------------------------------------------

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{CSInformationSign}[2022/02/25 Creodocs Information Sign Class v1.1]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}} % Pass through any extra options specified to the base class
\ProcessOptions\relax % Process class options

\LoadClass{article} % Load the base class

%----------------------------------------------------------------------------------------
%	PACKAGES AND OTHER DOCUMENT CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{etoolbox} % Required for conditional logic and easily changing commands

\usepackage[usenames, svgnames]{xcolor} % Required for defining and using custom colors

\usepackage{tikz} % Required for custom graphics

\pagestyle{empty} % Suppress headers and footers

% Suppress hyphenation across the whole document
\hyphenpenalty=10000
\exhyphenpenalty=10000

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage{geometry} % Required for adjusting page dimensions and margins

\geometry{
	top=2cm, % Top margin
	bottom=2.25cm, % Bottom margin
	left=2.25cm, % Left margin
	right=2.25cm, % Right margin
	%showframe, % Uncomment to show how the type block is set on the page
}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage{fontspec} % Required for specifying custom fonts

\defaultfontfeatures{Ligatures=TeX} % To support LaTeX ligatures (`` and --)
\defaultfontfeatures{Path=Fonts/} % Specify the location of font files

% Set the main sans font
\setmainfont{Merriweather}[
	UprightFont=*-Regular.otf,
	BoldFont=*-Bold.otf,
	ItalicFont=*-Italic.otf,
	BoldItalicFont=*-BoldItalic.otf
]

\newfontface\latoblack{Lato-Black.ttf} % Define a command for a single custom font

%---------------------------------------------------------------------------------
%	DOCUMENT CONTENT VARIABLES
%---------------------------------------------------------------------------------

\newcommand{\informationheading}[1]{\renewcommand{\informationheading}{#1}}
\newcommand{\informationtext}[1]{\renewcommand{\informationtext}{#1}}
\newcommand{\additionaltext}[1]{\renewcommand{\additionaltext}{#1}}
