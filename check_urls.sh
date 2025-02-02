#!/bin/bash

mkdir -p test-reports
urlchecker check \
    --file-types .rst,.md,.py \
    --save test-reports/url-check.csv \
    --exclude-files qps/pyqtgraph \
    --exclude-urls http://mrcc.com/qgis.dtd,https://bugreports.qt-project.org/browse/QTBUG-18616 \
    qps
