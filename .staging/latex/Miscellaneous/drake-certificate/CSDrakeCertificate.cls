%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Drake Certificate
% LaTeX Class
% Version 1.0 (February 24, 2022)
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
\ProvidesClass{CSDrakeCertificate}[2022/02/24 Creodocs Drake Certificate Class v1.0]

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

\usepackage{tikz} % Required for creation and precise placement of text and graphics
\usetikzlibrary{calc} % Required for adjusting relative positions of TikZ elements with +/- offsets

\setlength{\parindent}{0pt} % Suppress paragraph indentation

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage{geometry} % Required for adjusting page dimensions

\geometry{
	top=2.5cm, % Top margin
	bottom=1.5cm, % Bottom margin
	left=4.75cm, % Left margin
	right=4.75cm, % Right margin
	landscape, % Landscape page orientation
	%showframe, % Uncomment to show how the type block is set on the page
}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage[utf8]{inputenc} % Required for inputting international characters
\usepackage[T1]{fontenc} % Output font encoding for international characters

\usepackage[default, semibold]{sourceserifpro} % Use the Source Serif Pro as the default font with semibold for \bfseries
\newcommand{\sourceserifproblack}[1]{{\fontseries{k}\fontshape{n}\selectfont #1}} % New command for using the black font weight

\newcommand{\sourcesanspro}[1]{{\fontfamily{SourceSansPro-LF}\selectfont#1}} % Custom Source Sans Pro font command

\usepackage{microtype} % Improve justification

%----------------------------------------------------------------------------------------
%	CERTIFICATE FRAMING
%----------------------------------------------------------------------------------------

\newcommand{\outputframe}{
	\begin{tikzpicture}[remember picture, overlay]
		\draw[draw=black, line width=20pt] (current page.north west) rectangle (current page.south east); % Thick rectangle around the page
		
		\draw[draw=black, line width=2pt] ($(current page.north west)-(-15pt, 15pt)$) rectangle ($(current page.south east)+(-15pt, 15pt)$); % Outer thin rectangle
		\draw[draw=black, line width=2pt] ($(current page.north west)-(-21pt, 21pt)$) rectangle ($(current page.south east)+(-21pt, 21pt)$); % Middle thin rectangle
		\draw[draw=black, line width=2pt] ($(current page.north west)-(-27pt, 27pt)$) rectangle ($(current page.south east)+(-27pt, 27pt)$); % Inner thin rectangle
		
		\draw [fill=black] (current page.north west) -- ($(current page.north west)-(0cm, 3cm)$) -- ($(current page.north west)+(3cm, 0cm)$) -- cycle; % Top left triangle
		\draw [fill=black] (current page.north east) -- ($(current page.north east)-(0cm, 3cm)$) -- ($(current page.north east)-(3cm, 0cm)$) -- cycle; % Top right triangle
		\draw [fill=black] (current page.south west) -- ($(current page.south west)+(0cm, 3cm)$) -- ($(current page.south west)+(3cm, 0cm)$) -- cycle; % Bottom left triangle
		\draw [fill=black] (current page.south east) -- ($(current page.south east)+(0cm, 3cm)$) -- ($(current page.south east)-(3cm, 0cm)$) -- cycle; % Bottom right triangle
	\end{tikzpicture}
}

%----------------------------------------------------------------------------------------
%	DOCUMENT CONTENT VARIABLES
%----------------------------------------------------------------------------------------

\newcommand{\heading}[1]{\renewcommand{\heading}{#1}}
\newcommand{\subheading}[1]{\renewcommand{\subheading}{#1}}

\newcommand{\recipient}[1]{\renewcommand{\recipient}{#1}}

\newcommand{\largedescription}[1]{\renewcommand{\largedescription}{#1}}
\newcommand{\smalldescription}[1]{\renewcommand{\smalldescription}{#1}}

\newcommand{\leftlinetitle}[1]{\renewcommand{\leftlinetitle}{#1}}
\newcommand{\leftlineoptional}[1]{\renewcommand{\leftlineoptional}{#1}}
\newcommand{\rightlinetitle}[1]{\renewcommand{\rightlinetitle}{#1}}
\newcommand{\rightlineoptional}[1]{\renewcommand{\rightlineoptional}{#1}}
