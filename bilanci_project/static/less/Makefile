STYLES_LESS = ./main.less
STYLES_CSS = ../css/main.css
DATE=$(shell date +%I:%M%p)
CHECK=\033[32m✔\033[39m
HR=\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#

#
# BUILD DOCS
#

build:
	@echo "\n${HR}"
	@echo "Building Css..."
	@echo "${HR}\n"
	@lessc  ${STYLES_LESS} > ${STYLES_CSS}
	@echo "Compiling LESS with Recess...               ${CHECK} Done"
	@echo "Proyect styles successfully built at ${DATE}."
	@echo "${HR}\n"
	@echo "Thanks for using Recess,"

