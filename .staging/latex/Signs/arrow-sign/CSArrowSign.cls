%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Arrow Sign
% LaTeX Class
% Version 1.0 (March 17, 2022)
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
\ProvidesClass{CSArrowSign}[2022/03/17 Creodocs Arrow Sign Class v1.0]

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
\usetikzlibrary{shapes.arrows} % Required for drawing arrows

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage{geometry} % Required for adjusting page dimensions and margins

\geometry{
	paperwidth=29.7cm, % Paper width (can easily be made thinner or wider)
	paperheight=12cm, % Paper height (changing this requires adjusting a lot of things; not recommended)
	top=0cm, % Top margin
	bottom=0cm, % Bottom margin
	left=0cm, % Left margin
	right=0cm, % Right margin
	%showframe, % Uncomment to show how the type block is set on the page
}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage{fontspec} % Required for specifying custom fonts

\defaultfontfeatures{Ligatures=TeX} % To support LaTeX ligatures (e.g. `` and --)
\defaultfontfeatures{Path=Fonts/} % Specify the location of font files

\newfontface{\leaguegothic}{LeagueGothic-Regular.otf} % League Gothic Regular as the sign text font

%----------------------------------------------------------------------------------------
%	CREATE SIGN ARROW
%----------------------------------------------------------------------------------------

\newcommand{\signarrow}[5]{
	% Determine whether the arrow is to point left or (the default) right
	\expandafter\ifstrequal\expandafter{#5}{left}{
		\renewcommand{\rotationdegrees}{180} % Rotate 180 degrees to point left
	}{
		\renewcommand{\rotationdegrees}{0} % No rotation degrees to point right (the default)
	}
	{\topskip0pt\vspace*{\fill}} % Vertical centering on the page
	\begin{center} % Horizontally center on the page
		\begin{tikzpicture}
			% Large outer arrow
			\node[
				single arrow, % Shape type
				fill=#3, % Background color
				minimum width=0.95\paperheight, % Arrow height
				minimum height=0.95\paperwidth, % Arrow width
				inner sep=8pt, % Inner padding
				rotate=\rotationdegrees, % Rotation degrees
			] {};
			% Smaller inner arrow with border
			\node[
				single arrow, % Shape type
				draw=#4, % Border color
				line width=0.3cm, % Border thickness
				fill=#3, % Background color
				minimum width=0.75\paperheight, % Arrow height
				minimum height=0.91\paperwidth, % Arrow width
				inner sep=6pt, % Inner padding
				rotate=\rotationdegrees, % Rotation degrees
			] {};
			 % Sign text
			\node[
				font=\fontsize{#2}{#2}\selectfont\leaguegothic, % Text styling
				text=#4, % Text color
				align=flush center, % Horizontal text alignment
				text width=0.8\paperwidth, % Maximum text width
			] {\MakeUppercase{#1}}; % Sign text
		\end{tikzpicture}
	\end{center}
	\vspace*{\fill} % Vertical centering on the page
	\clearpage % New page if there is additional content after this
}

%---------------------------------------------------------------------------------
%	DOCUMENT CONTENT VARIABLES
%---------------------------------------------------------------------------------

\newcommand{\rotationdegrees}{}
