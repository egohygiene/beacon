%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Alert Sign
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
\ProvidesClass{CSAlertSign}[2022/02/25 Creodocs Alert Sign Class v1.1]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}} % Pass through any extra options specified to the base class
\ProcessOptions\relax % Process class options

\LoadClass{article} % Load the base class

%----------------------------------------------------------------------------------------
%	REQUIRED PACKAGES AND MISC CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{etoolbox} % Required for conditional logic and easily changing commands

% Suppress hyphenation across the whole document
\hyphenpenalty=10000
\exhyphenpenalty=10000

\pagestyle{empty} % Suppress headers and footers

\usepackage[usenames, svgnames]{xcolor} % Required for defining and using custom colors

\usepackage{tikz} % Required for custom graphics

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage{geometry} % Required for adjusting page dimensions and margins

\geometry{
	top=2.5cm, % Top margin
	bottom=3cm, % Bottom margin
	left=2.5cm, % Left margin
	right=2.5cm, % Right margin
	%showframe, % Uncomment to show how the type block is set on the page
}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage[utf8]{inputenc} % Required for inputting international characters
\usepackage[T1]{fontenc} % Output font encoding for international characters

\usepackage[default]{sourcesanspro} % Use the Source Sans Pro font

%---------------------------------------------------------------------------------
%	DOCUMENT CONTENT VARIABLES
%---------------------------------------------------------------------------------

\newcommand{\alertheading}[1]{\renewcommand{\alertheading}{#1}}
\newcommand{\alerttext}[1]{\renewcommand{\alerttext}{#1}}
\newcommand{\instructiontext}[1]{\renewcommand{\instructiontext}{#1}}
