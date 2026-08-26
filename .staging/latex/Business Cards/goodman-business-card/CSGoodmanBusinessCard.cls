%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Goodman Business Card
% LaTeX Class
% Version 1.0 (April 1, 2022)
%
% This class originates from:
% https://www.LaTeXTemplates.com
%
% Authors:
% Vel (vel@latextemplates.com)
% Candrika Pujnadati
%
% License:
% CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%----------------------------------------------------------------------------------------
%	CLASS CONFIGURATION
%----------------------------------------------------------------------------------------

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{CSGoodmanBusinessCard}[2022/04/01 Creodocs Goodman Business Card Class v1.0]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}} % Pass through any extra options specified to the base class
\ProcessOptions\relax % Process class options

\LoadClass[8pt]{extarticle} % Load the base class with the default font size

%----------------------------------------------------------------------------------------
%	REQUIRED PACKAGES AND MISC CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{etoolbox} % Required for conditional logic and easily changing commands

\usepackage{array} % Required for manipulating table columns

\setlength{\parindent}{0pt} % No paragraph indentation

\pagestyle{empty} % Suppress headers and footers

\raggedright % Suppress hyphenation

\makeatletter
\let\@minipagerestore=\raggedright % Ensure all text in minipages is left aligned without hyphenation
\makeatother

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage[
	top=0.25cm, % Top margin
	bottom=0.6cm, % Bottom margin
	left=0.5cm, % Left margin
	right=0.5cm, % Right margin
	%showframe % Uncomment to show frames around the margins for debugging purposes
]{geometry}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage[T1]{fontenc} % Output font encoding for international characters
\usepackage[utf8]{inputenc} % Required for inputting international characters

\usepackage[
	semibold, % Use SemiBold instead of Bold
	oldstyle, % Use oldstyle figures, i.e. numbers that descend below the baseline
]{ebgaramond} % Use the EB Garamond font

\usepackage{microtype} % Improve typography

%----------------------------------------------------------------------------------------
%	OUTPUT COMPANY NAME
%----------------------------------------------------------------------------------------

\newcommand{\outputcompany}[1]{
	\strut% A strut ensures consistent vertical alignment and acts as text even if no company is specified which preserves vertical spacing
	\hfill% Push the company name to the right
	\textbf{\textsc{#1}}% Company name 

	\vfill % Automatic vertical whitespace
}

%----------------------------------------------------------------------------------------
%	OUTPUT NAME LINE
%----------------------------------------------------------------------------------------

\newcommand{\outputnameline}[3]{{\fontsize{#2}{#3}\selectfont\MakeUppercase{#1}\par}} % Output an individual line of the name

%----------------------------------------------------------------------------------------
%	OUTPUT JOB TITLE
%----------------------------------------------------------------------------------------

\newcommand{\outputjobtitle}[2]{ % Output the job title
	\expandafter\ifstrequal\expandafter{#1}{}{}{ % If a job title was specified
		\vspace{2pt} % Vertical whitespace

		{\fontsize{#2}{#2}\selectfont\textit{#1}} % Job title
	}
	
	\vfill % Automatic vertical whitespace
}
